"""Confirmation emails for the GDPR self-service actions in this app.

Uses Django's console email backend by default (prints to the server log),
so this works out of the box without SMTP credentials. Set EMAIL_* in .env
for a real deployment - see config/settings.py.

Each email is written in its recipient's language, which is not always the
language of whoever caused it (a manager deleting an employee's account).

Sending is best-effort (`fail_silently=True`): the export/deletion the
person asked for has already happened by the time we try to notify them, and
a flaky mail relay shouldn't be able to make that fail or look like it did.
"""

from __future__ import annotations

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone, translation
from django.utils.formats import date_format
from django.utils.translation import gettext as _


def _send(subject: str, body: str, to: str) -> None:
    if not to:
        return
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [to], fail_silently=True)


def send_data_export_email(user) -> None:
    with translation.override(user.language or settings.LANGUAGE_CODE):
        when = date_format(timezone.localtime(), "DATETIME_FORMAT")
        _send(
            _("Your PlanShift data export"),
            _(
                "Hi %(name)s,\n\n"
                "A copy of your personal data was just downloaded from your PlanShift account (%(when)s).\n\n"
                "If this wasn't you, someone else may have access to your account - sign in and change your "
                "password, or contact your manager immediately.\n\n"
                "\u2014 PlanShift"
            )
            % {"name": user.display_name, "when": when},
            user.email,
        )


def send_account_deleted_email(email: str, name: str, language: str = "") -> None:
    with translation.override(language or settings.LANGUAGE_CODE):
        _send(
            _("Your PlanShift account has been deleted"),
            _(
                "Hi %(name)s,\n\n"
                "Your PlanShift account and the personal data associated with it (profile, shift assignments "
                "and unavailability) have been permanently deleted, as you requested.\n\n"
                "If you did not request this, contact your organisation's manager immediately.\n\n"
                "\u2014 PlanShift"
            )
            % {"name": name},
            email,
        )
