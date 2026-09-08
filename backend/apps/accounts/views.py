from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.frontend.shell import render_app
from apps.scheduling.models import Position

from .decorators import manager_required
from .debug_views import ensure_demo_accounts
from .forms import CreateEmployeeForm, UpdateEmployeeForm
from .models import User, UserRole


def _redirect_with_message(
    request: HttpRequest,
    *,
    level: int,
    text: str,
    to: str = "manager_employees",
) -> HttpResponse:
    messages.add_message(request, level, text)
    return redirect(to)

def _get_employee_or_404(user_id: int) -> User:
    qs = User.objects.select_related("position")
    return get_object_or_404(qs, pk=user_id, role=UserRole.EMPLOYEE)

def _store_one_time_credentials(request: HttpRequest, employee: User, password: str) -> None:
    request.session["one_time_credentials"] = {
        "login": employee.email,
        "password": password,
        "employee_id": employee.employee_id,
    }

def _login_urls() -> dict[str, str]:
    urls = {"login": reverse("login")}
    if settings.DEBUG:
        urls["demoManager"] = reverse("demo_login", args=["manager"])
        urls["demoEmployee"] = reverse("demo_login", args=["employee"])
    return urls


@require_http_methods(["GET", "POST"])
def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("home")

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("home")

    return render_app(
        request,
        entry="login",
        title="Login",
        description="Shift Management System Login",
        body_class="auth-body",
        data={
            "showDemo": settings.DEBUG,
            "username": form["username"].value() or "",
            "error": " ".join(form.non_field_errors()),
            "urls": _login_urls(),
        },
    )

@login_required
@require_POST
def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect("login")

@login_required
def home(request: HttpRequest) -> HttpResponse:
    if request.user.is_manager:
        return redirect("manager_shifts")
    return redirect("employee_shifts")

def _employee_payload(employees) -> list[dict]:
    return [
        {
            "id": employee.id,
            "employeeId": employee.employee_id,
            "fullName": employee.get_full_name() or employee.username,
            "email": employee.email,
            "positionId": employee.position_id,
            "position": employee.position.name if employee.position else "",
        }
        for employee in employees
    ]


@manager_required
@require_GET
def manager_employees(request: HttpRequest) -> HttpResponse:
    if settings.DEBUG:
        ensure_demo_accounts()

    creds = request.session.pop("one_time_credentials", None)
    employees = User.objects.filter(role=UserRole.EMPLOYEE).select_related("position")
    positions = Position.objects.order_by("name")

    return render_app(
        request,
        entry="manager-employees",
        title="Employee Management",
        description="Manage employees",
        nav_active="manager_employees",
        data={
            "employees": _employee_payload(employees),
            "positions": [{"id": p.id, "name": p.name} for p in positions],
            "credentials": {"login": creds["login"], "password": creds["password"]} if creds else None,
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
    form = CreateEmployeeForm(request.POST)
    if not form.is_valid():
        return _redirect_with_message(request, level=messages.ERROR, text="Please fix the errors and try again.")

    employee = form.save(commit=False)
    password = User.generate_password()
    employee.set_password(password)
    employee.save()
    _store_one_time_credentials(request, employee, password)
    return _redirect_with_message(request, level=messages.SUCCESS, text="Employee created.")

@manager_required
@require_POST
def employee_update(request: HttpRequest, user_id: int) -> HttpResponse:
    employee = _get_employee_or_404(user_id)
    form = UpdateEmployeeForm(request.POST, instance=employee)
    if not form.is_valid():
        return _redirect_with_message(request, level=messages.ERROR, text="Could not update employee.")
    form.save()
    return _redirect_with_message(request, level=messages.SUCCESS, text="Employee updated.")

@manager_required
@require_POST
def reset_employee_password(request: HttpRequest, user_id: int) -> HttpResponse:
    employee = _get_employee_or_404(user_id)
    password = User.generate_password()
    employee.set_password(password)
    employee.save(update_fields=["password"])

    _store_one_time_credentials(request, employee, password)
    return _redirect_with_message(request, level=messages.SUCCESS, text="Password reset.")

@manager_required
@require_POST
def employee_delete(request: HttpRequest, user_id: int) -> HttpResponse:
    employee = _get_employee_or_404(user_id)
    label = employee.get_full_name() or employee.username
    employee.delete()
    return _redirect_with_message(request, level=messages.SUCCESS, text=f"Deleted employee: {label}.")
