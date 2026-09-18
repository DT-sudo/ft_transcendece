"""Sign-up, login, logout, demo logins, and the admin-side account and position directory."""

from __future__ import annotations

from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.notifications.services import managers, notify
from apps.privacy.emails import send_account_deleted_email
from apps.realtime.events import DIRECTORY_CHANGED, notify_everyone
from apps.shell import field_errors, first_form_error, flash_redirect, render_app
from apps.scheduling import notices
from apps.scheduling.management.commands.seed_demo import DEMO_ACCOUNTS, DEMO_EMPLOYEE_EMAIL
from apps.twofactor import services as two_factor
from apps.twofactor.views import begin_login

from .forms import EmailAuthenticationForm, PositionForm, SignUpForm, UserForm
from .models import MANAGER_POSITION_NAME, Position, User, UserRole
from .security import end_sessions, end_sessions_for, end_this_session, log_security
from .services import delete_position, position_options, release_from_upcoming

# ── Role decorators ─────────────────────────────────────────────────────────


def _home_page(user) -> str:
    """The page that holds this account's own work: accounts, the schedule, or your shifts."""
    if user.is_admin:
        return "manager_employees"
    return "manager_shifts" if user.is_manager else "employee_shifts"


def _requires(allowed):
    """Require login and a role; anyone else is sent to their own home page."""

    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")
            if not allowed(request.user):
                return redirect(_home_page(request.user))
            return view(request, *args, **kwargs)

        return wrapped

    return decorator


# The three jobs the app is split into: admins provision accounts and positions, managers run
# the schedule, employees work it. Colleagues (friends) are for the two who actually work here.
admin_required = _requires(lambda user: user.is_admin)
manager_required = _requires(lambda user: user.is_manager and not user.is_admin)
employee_required = _requires(lambda user: user.is_employee)
non_admin_required = _requires(lambda user: not user.is_admin)


# ── Authentication ──────────────────────────────────────────────────────────


@require_http_methods(["GET", "POST"])
def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("home")

    form = EmailAuthenticationForm(request, data=request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            log_security("login.password_ok", request, actor=form.get_user())
            # With two-factor authentication on, this only leads to the code step.
            return begin_login(request, form.get_user())
        log_security("login.failed", request, email=form["username"].value() or "-")

    # AuthenticationForm calls the field `username`; the UI calls it `email`.
    errors = field_errors(form)
    if "username" in errors:
        errors["email"] = errors.pop("username")

    urls = {"login": reverse("login"), "signup": reverse("signup")}
    if settings.ENABLE_DEMO_LOGIN:
        # demoAdmin, demoManager, demoEmployee
        urls.update({f"demo{role.title()}": reverse("demo_login", args=[role]) for role in DEMO_ACCOUNTS})

    return render_app(
        request,
        page="login",
        title=_("Sign in"),
        data={
            "showDemo": settings.ENABLE_DEMO_LOGIN,
            "email": form["username"].value() or "",
            "error": " ".join(form.non_field_errors()),
            "fieldErrors": errors,
            "urls": urls,
        },
    )


@require_http_methods(["GET", "POST"])
def signup_view(request: HttpRequest) -> HttpResponse:
    """Open a manager account: email + password, hashed by Django's PBKDF2."""
    if request.user.is_authenticated:
        return redirect("home")

    posted = request.method == "POST"
    form = SignUpForm(request.POST or None)
    if posted and form.is_valid():
        user = form.save()
        login(request, user)
        log_security("signup", request, actor=user, role=user.role)
        messages.success(request, _("Welcome, %(name)s. Your account is ready.") % {"name": user.get_full_name()})
        return redirect("home")

    return render_app(
        request,
        page="signup",
        title=_("Create account"),
        data={
            "values": {
                "fullName": request.POST.get("full_name", ""),
                "email": request.POST.get("email", ""),
            },
            "error": " ".join(form.non_field_errors()) if posted else "",
            "fieldErrors": field_errors(form) if posted else {},
            "urls": {"signup": reverse("signup"), "login": reverse("login")},
        },
    )


@login_required
@require_POST
def logout_view(request: HttpRequest) -> HttpResponse:
    # Every tab of this browser session leaves with it, not just the one that pressed the button.
    end_this_session(request)
    log_security("logout", request)
    logout(request)
    return redirect("login")


@login_required
def home(request: HttpRequest) -> HttpResponse:
    """Send each role to its own landing page."""
    return redirect(_home_page(request.user))


# ── Demo accounts (ENABLE_DEMO_LOGIN) ───────────────────────────────────────


@require_GET
def demo_login(request: HttpRequest, role: str) -> HttpResponse:
    """Sign in as one of the accounts `seed_demo` creates, without a password (but not without a 2FA code)."""
    if not settings.ENABLE_DEMO_LOGIN:
        return redirect("login")
    email = DEMO_ACCOUNTS.get(role, DEMO_EMPLOYEE_EMAIL)
    user = User.objects.filter(username=email, is_active=True).first()
    if user is None:
        messages.error(request, _("Demo accounts are missing. Run `python manage.py seed_demo` first."))
        return redirect("login")
    log_security("login.demo", request, actor=user, role=role)
    return begin_login(request, user)


# ── Accounts (admins) ───────────────────────────────────────────────────────


def _managed_user_or_404(request: HttpRequest, user_id: int) -> User:
    return get_object_or_404(request.user.managed_users(), pk=user_id)


def _set_generated_password(request: HttpRequest, employee: User) -> None:
    """Give the employee a fresh random password and keep it in the session to show once."""
    password = User.generate_password()
    employee.set_password(password)
    employee.save()
    request.session["one_time_credentials"] = {"login": employee.email, "password": password}


def _back(request: HttpRequest, level: int, text: str) -> HttpResponse:
    return flash_redirect(request, level, text, "manager_employees")


def _directory_changed() -> None:
    """Every open page re-reads itself: the accounts and positions directory is shared by all three roles."""
    notify_everyone(DIRECTORY_CHANGED)


@admin_required
@require_GET
def manager_employees(request: HttpRequest) -> HttpResponse:
    return render_app(
        request,
        page="manager-employees",
        title=_("User Management"),
        nav_active="manager_employees",
        data={
            "employees": [
                {
                    "id": e.id,
                    "employeeId": e.employee_id,
                    "fullName": e.display_name,
                    "avatarUrl": e.avatar_url,
                    "profileUrl": reverse("profile", args=[e.id]),
                    "email": e.email,
                    "role": e.role,
                    "roleLabel": e.get_role_display(),
                    "positionId": e.position_id,
                    "position": e.position.name if e.position else "",
                    "twoFactor": two_factor.is_enabled(e),
                }
                for e in request.user.managed_users().select_related("position", "totp_device")
            ],
            "roles": [{"id": value, "name": label} for value, label in UserRole.choices],
            "positions": position_options(),
            "credentials": request.session.pop("one_time_credentials", None),
            "urls": {
                "create": reverse("manager_employees_create"),
                "update": reverse("employee_update", args=[0]),
                "delete": reverse("employee_delete", args=[0]),
                "resetPassword": reverse("reset_employee_password", args=[0]),
                "resetTwoFactor": reverse("reset_employee_two_factor", args=[0]),
                "positionCreate": reverse("position_create"),
                "positionDelete": reverse("position_delete", args=[0]),
            },
        },
    )


@admin_required
@require_POST
def manager_employees_create(request: HttpRequest) -> HttpResponse:
    form = UserForm(request.POST)
    if not form.is_valid():
        return _back(request, messages.ERROR, first_form_error(form, _("Please fix the errors and try again.")))

    account = form.save(commit=False)
    _set_generated_password(request, account)
    notify(managers(), "account.added", actor=request.user, role=account.role, name=account.display_name)
    _directory_changed()
    log_security("account.created", request, target=account, role=account.role)
    return _back(request, messages.SUCCESS, _("%(role)s created.") % {"role": account.get_role_display()})


@admin_required
@require_POST
def employee_update(request: HttpRequest, user_id: int) -> HttpResponse:
    account = _managed_user_or_404(request, user_id)
    # Read before validating: the posted values are written onto the instance by the form.
    was_role, was_position_id = account.role, account.position_id

    form = UserForm(request.POST, instance=account)
    if not form.is_valid():
        return _back(request, messages.ERROR, first_form_error(form, _("Could not update the account.")))
    account = form.save()

    role_changed = account.role != was_role
    # A promotion clears the position, which `role_changed` already covers; this is the
    # plain case of an employee given a different job title.
    position_changed = account.position_id != was_position_id

    if role_changed or position_changed:
        # The shifts ahead were booked against the role and position the account no longer has.
        release_from_upcoming(account, actor=request.user)
    if role_changed:
        # The pages of the old role must stop answering for this account at once - including
        # the copy its browser might hand back on the Back button.
        end_sessions(account, reason="role_changed", request=request)
        log_security("account.role_changed", request, target=account, was=was_role, now=account.role)

    if form.has_changed():
        actor = request.user
        notify(managers(), "account.updated", actor=actor, role=account.role, name=account.display_name)
        if role_changed:
            notify([account], "account.role_changed", actor=actor, by=actor.display_name, role=account.role)
        elif position_changed and account.position:
            notify(
                [account], "account.position_changed", actor=actor, by=actor.display_name, position=account.position.name
            )
        else:
            notify([account], "account.details_updated", actor=actor, by=actor.display_name)
        _directory_changed()
        log_security("account.updated", request, target=account, fields=",".join(form.changed_data) or "-")
    return _back(request, messages.SUCCESS, _("%(role)s updated.") % {"role": account.get_role_display()})


@admin_required
@require_POST
def reset_employee_password(request: HttpRequest, user_id: int) -> HttpResponse:
    employee = _managed_user_or_404(request, user_id)
    _set_generated_password(request, employee)
    # A new password ends the old sessions; this is what makes their open tabs notice.
    end_sessions(employee, reason="password_reset", request=request)
    notify([employee], "account.password_reset", actor=request.user, level="warning", by=request.user.display_name)
    return _back(request, messages.SUCCESS, _("Password reset."))


@admin_required
@require_POST
def reset_employee_two_factor(request: HttpRequest, user_id: int) -> HttpResponse:
    """Turn off 2FA for someone who lost both their phone and their recovery codes; they are told by email."""
    account = _managed_user_or_404(request, user_id)
    if not two_factor.disable(account, actor=request.user):
        return _back(request, messages.ERROR, _("%(name)s doesn't use two-factor authentication.") % {"name": account.display_name})
    _directory_changed()
    log_security("account.two_factor_reset", request, target=account)
    return _back(request, messages.SUCCESS, _("Two-factor authentication reset for %(name)s.") % {"name": account.display_name})


@admin_required
@require_POST
def employee_delete(request: HttpRequest, user_id: int) -> HttpResponse:
    """Erase an account on the admin's initiative.

    This is the other door to the same GDPR erasure right as
    `apps.privacy.delete_my_account` - the Privacy Policy tells users they can
    ask their manager to delete their account directly instead of using the
    self-service page - so it closes with the same confirmation email, sent
    to the employee (not the manager) once the data is actually gone.
    """
    account = _managed_user_or_404(request, user_id)
    account_id = account.pk
    label, email, role, language = account.display_name, account.email, account.role, account.language
    role_label = str(account.get_role_display())
    # The upcoming shifts they leave need someone else; the managers are told which.
    release_from_upcoming(account, actor=request.user, tell_account=False)
    # Their worked assignments go with them (Assignment.employee is CASCADE), so the calendars change.
    had_assignments = account.assignments.exists()
    account.delete()
    # Nothing is left to authorise their open pages; they go to the sign-in page rather
    # than sitting on a view of an account that no longer exists.
    end_sessions_for(account_id, reason="account_deleted", request=request)
    send_account_deleted_email(email, label, language)
    notify(managers(), "account.deleted", actor=request.user, level="warning", role=role, name=label)
    _directory_changed()
    if had_assignments:
        notices.shifts_changed()
    log_security("account.deleted", request, account=account_id, role=role)
    return _back(request, messages.SUCCESS, _("Deleted %(role)s: %(name)s.") % {"role": role_label.lower(), "name": label})


# ── Positions (Users page) ──────────────────────────────────────────────────


@admin_required
@require_POST
def position_create(request: HttpRequest) -> HttpResponse:
    form = PositionForm(request.POST)
    if not form.is_valid():
        return _back(request, messages.ERROR, first_form_error(form, _("Could not create position.")))
    position = form.save()
    notify(managers(), "position.created", actor=request.user, name=position.name)
    _directory_changed()
    log_security("position.created", request, position=position.pk)
    return _back(request, messages.SUCCESS, _("Position created: %(name)s.") % {"name": position.name})


@admin_required
@require_POST
def position_delete(request: HttpRequest, position_id: int) -> HttpResponse:
    position = get_object_or_404(Position, pk=position_id)
    if position.name == MANAGER_POSITION_NAME:
        return _back(request, messages.ERROR, _("The Manager position can't be deleted."))
    delete_position(position, actor=request.user)
    _directory_changed()
    log_security("position.deleted", request, position=position_id)
    return _back(request, messages.SUCCESS, _("Position deleted: %(name)s.") % {"name": position.name})
