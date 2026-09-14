from __future__ import annotations

import secrets
import string
import uuid
from pathlib import Path

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.urls import reverse

def generate_employee_id() -> str:
    return f"EMP-{secrets.randbelow(900000) + 100000}"

def avatar_path(user: User, filename: str) -> str:
    # Random names: the path says nothing about its owner, and a new picture never reuses an old URL.
    return f"avatars/{uuid.uuid4().hex}.webp"

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
    bio = models.CharField(max_length=300, blank=True)
    # Always a 256x256 WebP re-encoded by `apps.profiles.avatars`; empty means the initials default.
    avatar = models.ImageField(upload_to=avatar_path, blank=True)
    # Online status (`apps.profiles.presence`): open sockets, and when one last confirmed it is alive.
    open_sockets = models.PositiveIntegerField(default=0, editable=False)
    last_seen = models.DateTimeField(null=True, blank=True, editable=False)
    @property
    def display_name(self) -> str:
        return self.get_full_name() or self.username
    @property
    def role_label(self) -> str:
        """The line under a name: an employee's position, otherwise the role."""
        return self.position.name if self.is_employee and self.position else self.get_role_display()
    @property
    def avatar_url(self) -> str | None:
        if not self.avatar:
            return None
        # The file name changes with every upload, so it doubles as a cache buster.
        return f"{reverse('avatar', args=[self.pk])}?v={Path(self.avatar.name).stem}"
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


@receiver(post_delete, sender=User)
def _delete_avatar_file(sender, instance: User, **kwargs) -> None:
    """Erasing an account erases its picture too, whichever view deleted it."""
    if instance.avatar:
        instance.avatar.delete(save=False)
