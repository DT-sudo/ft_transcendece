"""Confirmation emails for the GDPR self-service actions in this app.

Uses Django's console email backend by default (prints to the server log),
so this works out of the box without SMTP credentials. Set EMAIL_* in .env
for a real deployment - see config/settings.py.

Sending is best-effort (`fail_silently=True`): the export/deletion the
person asked for has already happened by the time we try to notify them, and
a flaky mail relay shouldn't be able to make that fail or look like it did.
"""

from __future__ import annotations

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone


def _send(subject: str, body: str, to: str) -> None:
    if not to:
        return
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [to], fail_silently=True)


def send_data_export_email(user) -> None:
    when = timezone.now().strftime("%d %b %Y, %H:%M %Z")
    _send(
        "Your PlanShift data export",
        f"Hi {user.display_name},\n\n"
        f"A copy of your personal data was just downloaded from your PlanShift account ({when}).\n\n"
        "If this wasn't you, someone else may have access to your account - sign in and change your "
        "password, or contact your manager immediately.\n\n"
        "\u2014 PlanShift",
        user.email,
    )


def send_account_deleted_email(email: str, name: str) -> None:
    _send(
        "Your PlanShift account has been deleted",
        f"Hi {name},\n\n"
        "Your PlanShift account and the personal data associated with it (profile, shift assignments "
        "and unavailability) have been permanently deleted, as you requested.\n\n"
        "If you did not request this, contact your organisation's manager immediately.\n\n"
        "\u2014 PlanShift",
        email,
    )
