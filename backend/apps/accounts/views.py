"""Sign-up, login, logout, demo logins, and the manager-side employee directory."""

from __future__ import annotations

from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import ProtectedError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.privacy.emails import send_account_deleted_email
from apps.shell import field_errors, first_form_error, flash_redirect, render_app
from apps.scheduling.management.commands.seed_demo import DEMO_ACCOUNTS, DEMO_EMPLOYEE_EMAIL
from apps.scheduling.services import position_options

from .forms import EmailAuthenticationForm, EmployeeForm, SignUpForm, UserForm
from .models import User, UserRole

# ── Role decorators ─────────────────────────────────────────────────────────


def _role_required(attr: str, other_home: str):
    """Require login and a role; a signed-in user of the other role goes to their own home."""

    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")
            if not getattr(request.user, attr):
                return redirect(other_home)
            return view(request, *args, **kwargs)

        return wrapped

    return decorator


manager_required = _role_required("is_manager", "employee_shifts")
employee_required = _role_required("is_employee", "manager_shifts")


# ── Authentication ──────────────────────────────────────────────────────────


@require_http_methods(["GET", "POST"])
def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("home")

    form = EmailAuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("home")

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
        title="Login",
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
        messages.success(request, f"Welcome, {user.get_full_name()}. Your account is ready.")
        return redirect("home")

    return render_app(
        request,
        page="signup",
        title="Create account",
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
    logout(request)
    return redirect("login")


@login_required
def home(request: HttpRequest) -> HttpResponse:
    """Send each role to its own landing page."""
    return redirect("manager_shifts" if request.user.is_manager else "employee_shifts")


# ── Demo accounts (ENABLE_DEMO_LOGIN) ───────────────────────────────────────


@require_GET
def demo_login(request: HttpRequest, role: str) -> HttpResponse:
    """Sign in as one of the accounts `seed_demo` creates, without a password."""
    if not settings.ENABLE_DEMO_LOGIN:
        return redirect("login")
    email = DEMO_ACCOUNTS.get(role, DEMO_EMPLOYEE_EMAIL)
    user = User.objects.filter(username=email, is_active=True).first()
    if user is None:
        messages.error(request, "Demo accounts are missing. Run `python manage.py seed_demo` first.")
        return redirect("login")
    login(request, user)
    return redirect("home")


# ── Employee directory (managers) ───────────────────────────────────────────


def _managed_user_or_404(request: HttpRequest, user_id: int) -> User:
    return get_object_or_404(request.user.managed_users(), pk=user_id)


def _account_form(request: HttpRequest):
    """Admins also pick the role; a manager's form always makes an employee (the model's default role)."""
    return UserForm if request.user.is_admin else EmployeeForm


def _set_generated_password(request: HttpRequest, employee: User) -> None:
    """Give the employee a fresh random password and keep it in the session to show once."""
    password = User.generate_password()
    employee.set_password(password)
    employee.save()
    request.session["one_time_credentials"] = {"login": employee.email, "password": password}


def _back(request: HttpRequest, level: int, text: str) -> HttpResponse:
    return flash_redirect(request, level, text, "manager_employees")


@manager_required
@require_GET
def manager_employees(request: HttpRequest) -> HttpResponse:
    is_admin = request.user.is_admin

    return render_app(
        request,
        page="manager-employees",
        title="User Management" if is_admin else "Employee Management",
        nav_active="manager_employees",
        data={
            "employees": [
                {
                    "id": e.id,
                    "employeeId": e.employee_id,
                    "fullName": e.display_name,
                    "email": e.email,
                    "role": e.role,
                    "roleLabel": e.get_role_display(),
                    "positionId": e.position_id,
                    "position": e.position.name if e.position else "",
                }
                for e in request.user.managed_users().select_related("position")
            ],
            # Present only for admins, who can assign roles.
            "roles": [{"id": value, "name": label} for value, label in UserRole.choices] if is_admin else None,
            "positions": position_options(),
            "credentials": request.session.pop("one_time_credentials", None),
            "urls": {
                "create": reverse("manager_employees_create"),
                "update": reverse("employee_update", args=[0]),
                "delete": reverse("employee_delete", args=[0]),
                "resetPassword": reverse("reset_employee_password", args=[0]),
                "positionCreate": reverse("position_create"),
                "positionDelete": reverse("position_delete", args=[0]),
            },
        },
    )


@manager_required
@require_POST
def manager_employees_create(request: HttpRequest) -> HttpResponse:
    form = _account_form(request)(request.POST)
    if not form.is_valid():
        return _back(request, messages.ERROR, first_form_error(form, "Please fix the errors and try again."))

    account = form.save(commit=False)
    _set_generated_password(request, account)
    return _back(request, messages.SUCCESS, f"{account.get_role_display()} created.")


@manager_required
@require_POST
def employee_update(request: HttpRequest, user_id: int) -> HttpResponse:
    account = _managed_user_or_404(request, user_id)
    form = _account_form(request)(request.POST, instance=account)
    if not form.is_valid():
        return _back(request, messages.ERROR, first_form_error(form, "Could not update the account."))
    account = form.save()
    return _back(request, messages.SUCCESS, f"{account.get_role_display()} updated.")


@manager_required
@require_POST
def reset_employee_password(request: HttpRequest, user_id: int) -> HttpResponse:
    employee = _managed_user_or_404(request, user_id)
    _set_generated_password(request, employee)
    return _back(request, messages.SUCCESS, "Password reset.")


@manager_required
@require_POST
def employee_delete(request: HttpRequest, user_id: int) -> HttpResponse:
    """Erase an employee's account on the manager's initiative.

    This is the other door to the same GDPR erasure right as
    `apps.privacy.delete_my_account` - the Privacy Policy tells users they can
    ask their manager to delete their account directly instead of using the
    self-service page - so it closes with the same confirmation email, sent
    to the employee (not the manager) once the data is actually gone.
    """
    account = _managed_user_or_404(request, user_id)
    label, email, role = account.display_name, account.email, account.get_role_display()
    try:
        account.delete()
    except ProtectedError:
        # Shift.created_by is PROTECT: a manager's schedule outlives a careless delete.
        return _back(request, messages.ERROR, f"Cannot delete {label}: they still have shifts. Reassign or delete them first.")
    send_account_deleted_email(email, label)
    return _back(request, messages.SUCCESS, f"Deleted {role.lower()}: {label}.")
