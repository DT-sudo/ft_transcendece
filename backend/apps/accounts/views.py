"""Sign-up, login, logout, demo logins, and the manager-side employee directory."""

from __future__ import annotations

from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.shell import field_errors, first_form_error, flash_redirect, render_app
from apps.scheduling.management.commands.seed_demo import DEMO_EMPLOYEE_EMAIL, DEMO_MANAGER_EMAIL
from apps.scheduling.models import Position

from .forms import EmailAuthenticationForm, EmployeeForm, SignUpForm
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
        urls["demoManager"] = reverse("demo_login", args=["manager"])
        urls["demoEmployee"] = reverse("demo_login", args=["employee"])

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
    email = DEMO_MANAGER_EMAIL if role == "manager" else DEMO_EMPLOYEE_EMAIL
    user = User.objects.filter(username=email, is_active=True).first()
    if user is None:
        messages.error(request, "Demo accounts are missing. Run `python manage.py seed_demo` first.")
        return redirect("login")
    login(request, user)
    return redirect("home")


# ── Employee directory (managers) ───────────────────────────────────────────


def _get_employee_or_404(user_id: int) -> User:
    return get_object_or_404(User, pk=user_id, role=UserRole.EMPLOYEE)


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
    employees = User.objects.filter(role=UserRole.EMPLOYEE).select_related("position")

    return render_app(
        request,
        page="manager-employees",
        title="Employee Management",
        nav_active="manager_employees",
        data={
            "employees": [
                {
                    "id": e.id,
                    "employeeId": e.employee_id,
                    "fullName": e.get_full_name() or e.username,
                    "email": e.email,
                    "positionId": e.position_id,
                    "position": e.position.name if e.position else "",
                }
                for e in employees
            ],
            "positions": [{"id": p.id, "name": p.name} for p in Position.objects.order_by("name")],
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
    form = EmployeeForm(request.POST)
    if not form.is_valid():
        return _back(request, messages.ERROR, first_form_error(form, "Please fix the errors and try again."))

    employee = form.save(commit=False)
    employee.role = UserRole.EMPLOYEE
    _set_generated_password(request, employee)
    return _back(request, messages.SUCCESS, "Employee created.")


@manager_required
@require_POST
def employee_update(request: HttpRequest, user_id: int) -> HttpResponse:
    form = EmployeeForm(request.POST, instance=_get_employee_or_404(user_id))
    if not form.is_valid():
        return _back(request, messages.ERROR, first_form_error(form, "Could not update employee."))
    form.save()
    return _back(request, messages.SUCCESS, "Employee updated.")


@manager_required
@require_POST
def reset_employee_password(request: HttpRequest, user_id: int) -> HttpResponse:
    _set_generated_password(request, _get_employee_or_404(user_id))
    return _back(request, messages.SUCCESS, "Password reset.")


@manager_required
@require_POST
def employee_delete(request: HttpRequest, user_id: int) -> HttpResponse:
    employee = _get_employee_or_404(user_id)
    label = employee.get_full_name() or employee.username
    employee.delete()
    return _back(request, messages.SUCCESS, f"Deleted employee: {label}.")
