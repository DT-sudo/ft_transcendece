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
from django.utils.translation import gettext_lazy as _

def generate_employee_id() -> str:
    return f"EMP-{secrets.randbelow(900000) + 100000}"

def avatar_path(user: User, filename: str) -> str:
    # Random names: the path says nothing about its owner, and a new picture never reuses an old URL.
    return f"avatars/{uuid.uuid4().hex}.webp"

class UserRole(models.TextChoices):
    ADMIN = "admin", _("Admin")
    MANAGER = "manager", _("Manager")
    EMPLOYEE = "employee", _("Employee")


# Manager-level accounts. Managers run the schedule; admins provision the accounts and positions.
MANAGER_ROLES = (UserRole.ADMIN, UserRole.MANAGER)

# A permanent, undeletable Position: giving it to an employee promotes the account to
# Manager instead of assigning a job title (see `UserForm.save`).
MANAGER_POSITION_NAME = "Manager"

class Position(models.Model):
    """A job title the admin keeps, e.g. "Barista". Shifts (apps.scheduling) reference it read-only."""

    name = models.CharField(max_length=25, unique=True)

    def __str__(self) -> str:
        return self.name

class User(AbstractUser):
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.EMPLOYEE)
    employee_id = models.CharField(max_length=20, unique=True, default=generate_employee_id, editable=False)
    position = models.ForeignKey(
        Position,
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
    # One of settings.LANGUAGES; empty until the first signed-in request (apps.i18n.middleware).
    # Emails and live notifications to this user are written in it.
    language = models.CharField(max_length=8, blank=True)
    @property
    def display_name(self) -> str:
        return self.get_full_name() or self.username
    @property
    def role_label(self) -> str:
        """The line under a name: an employee's position, otherwise the role."""
        return self.position.name if self.is_employee and self.position else str(self.get_role_display())
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
        """Manager level: managers, who run the schedule, and admins, who manage the accounts."""
        return self.role in MANAGER_ROLES
    @property
    def is_employee(self) -> bool:
        return self.role == UserRole.EMPLOYEE
    def managed_users(self) -> models.QuerySet[User]:
        """The accounts on the admin's Users page: every account but their own.

        Provisioning accounts is the admin's job alone; managers run the schedule. Nobody
        manages their own account here, so an admin can't demote or delete themselves
        (their own data is under "Privacy & my data").
        """
        if not self.is_admin:
            return User.objects.none()
        return User.objects.exclude(pk=self.pk)
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
