"""Give an existing account the admin role: `python manage.py make_admin someone@example.com`.

Sign-up only ever opens manager accounts, so this is how a deployment gets its first admin;
from then on admins assign roles from the Users page.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import User, UserRole


class Command(BaseCommand):
    help = "Make an existing account an admin, who can manage every account and its role."

    def add_arguments(self, parser) -> None:
        parser.add_argument("email")

    def handle(self, *args, email: str, **options) -> None:
        if not User.objects.filter(username=email.strip().lower()).update(role=UserRole.ADMIN, position=None):
            raise CommandError(f"No account with the email {email}.")
        self.stdout.write(self.style.SUCCESS(f"{email} is now an admin."))
