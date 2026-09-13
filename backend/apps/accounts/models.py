from __future__ import annotations

import secrets
import string

from django.contrib.auth.models import AbstractUser
from django.db import models

def generate_employee_id() -> str:
    return f"EMP-{secrets.randbelow(900000) + 100000}"

class UserRole(models.TextChoices):
    ADMIN = "admin", "Admin"
    MANAGER = "manager", "Manager"
    EMPLOYEE = "employee", "Employee"


# Admins run the schedule like managers, and also manage every account and its role.
MANAGER_ROLES = (UserRole.ADMIN, UserRole.MANAGER)

class User(AbstractUser):
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.EMPLOYEE)
    employee_id = models.CharField(max_length=20, unique=True, default=generate_employee_id, editable=False)
    position = models.ForeignKey(
        "scheduling.Position",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
    )
    @property
    def display_name(self) -> str:
        return self.get_full_name() or self.username
    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN
    @property
    def is_manager(self) -> bool:
        """Runs the schedule: managers and admins."""
        return self.role in MANAGER_ROLES
    @property
    def is_employee(self) -> bool:
        return self.role == UserRole.EMPLOYEE
    def managed_users(self) -> models.QuerySet[User]:
        """The accounts on this user's Team page: every other account for an admin, employees for a manager.

        Nobody manages their own account there, so an admin can't demote or delete themselves
        (their own data is under "Privacy & my data").
        """
        if not self.is_manager:
            return User.objects.none()
        accounts = User.objects.all() if self.is_admin else User.objects.filter(role=UserRole.EMPLOYEE)
        return accounts.exclude(pk=self.pk)
    def manages(self, other: User) -> bool:
        return self.managed_users().filter(pk=other.pk).exists()
    @staticmethod
    def generate_password(length: int = 14) -> str:
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))
