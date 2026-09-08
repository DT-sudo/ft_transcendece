from __future__ import annotations

from django.conf import settings
from django.contrib.auth import login
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_GET

from apps.scheduling.models import Position

from .models import User, UserRole


DEMO_PASSWORD = "demo12345!"
DEMO_MANAGER_USERNAME = "manager_demo@example.com"
DEMO_EMPLOYEE_USERNAME = "employee_demo@example.com"


def ensure_demo_accounts() -> tuple[User, User]:
    """Ensure both demo accounts exist and keep Demo admin as the only Django admin user."""
    barista, _ = Position.objects.get_or_create(name="Barista", defaults={"is_active": True})

    manager, manager_created = User.objects.get_or_create(
        username=DEMO_MANAGER_USERNAME,
        defaults={
            "email": DEMO_MANAGER_USERNAME,
            "first_name": "Demo",
            "last_name": "Admin",
            "role": UserRole.MANAGER,
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        },
    )
    manager.email = DEMO_MANAGER_USERNAME
    manager.first_name = "Demo"
    manager.last_name = "Admin"
    manager.role = UserRole.MANAGER
    manager.is_active = True
    manager.is_staff = True
    manager.is_superuser = True
    # Do not rewrite password hash on every request: it invalidates active sessions.
    if manager_created or not manager.check_password(DEMO_PASSWORD):
        manager.set_password(DEMO_PASSWORD)
    manager.save()

    # Keep a single Django admin account in the system.
    User.objects.exclude(pk=manager.pk).filter(Q(is_staff=True) | Q(is_superuser=True)).update(
        is_staff=False,
        is_superuser=False,
    )

    employee, employee_created = User.objects.get_or_create(
        username=DEMO_EMPLOYEE_USERNAME,
        defaults={
            "email": DEMO_EMPLOYEE_USERNAME,
            "first_name": "Demo",
            "last_name": "Employee",
            "role": UserRole.EMPLOYEE,
            "position": barista,
            "is_active": True,
        },
    )
    employee.email = DEMO_EMPLOYEE_USERNAME
    employee.first_name = "Demo"
    employee.last_name = "Employee"
    employee.role = UserRole.EMPLOYEE
    employee.position = employee.position or barista
    employee.is_active = True
    employee.is_staff = False
    employee.is_superuser = False
    if employee_created or not employee.check_password(DEMO_PASSWORD):
        employee.set_password(DEMO_PASSWORD)
    employee.save()

    return manager, employee


@require_GET
def demo_login(request: HttpRequest, role: str) -> HttpResponse:
    if not settings.ENABLE_DEMO_LOGIN:
        return redirect("login")
    manager, employee = ensure_demo_accounts()
    user = manager if role == "manager" else employee
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return redirect("home")
