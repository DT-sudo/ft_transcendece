"""Two-factor authentication: turning it on and off, checking codes, recovery codes."""

from __future__ import annotations

import enum
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone, translation
from django.utils.crypto import salted_hmac
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from apps.accounts.models import User
from apps.notifications.messages import render
from apps.notifications.services import notify

from . import totp
from .models import RecoveryCode, TOTPDevice

MAX_FAILED_ATTEMPTS = 5
LOCK_DURATION = timedelta(minutes=5)
LOCKED_MESSAGE = gettext_lazy("Too many incorrect codes. Wait 5 minutes, then try again.")

RECOVERY_CODE_COUNT = 10
# No 0/o, 1/i/l: the codes get written down on paper and typed back.
RECOVERY_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"


class Result(enum.Enum):
    CODE = "code"
    RECOVERY_CODE = "recovery_code"
    INVALID = "invalid"
    LOCKED = "locked"

    @property
    def ok(self) -> bool:
        return self in (Result.CODE, Result.RECOVERY_CODE)


def is_enabled(user: User) -> bool:
    # Reverse one-to-one: one query, cached on the instance (or none after select_related("totp_device")).
    return hasattr(user, "totp_device")


def normalize(code: str) -> str:
    """Codes are accepted with spaces or dashes ("123 456", "abcde-fghjk") and in any case."""
    return "".join((code or "").split()).replace("-", "").lower()


def _hash(code: str) -> str:
    # Keyed with SECRET_KEY: a leaked database alone doesn't allow testing guesses offline.
    return salted_hmac("apps.twofactor.RecoveryCode", normalize(code), algorithm="sha256").hexdigest()


def _replace_recovery_codes(device: TOTPDevice) -> list[str]:
    codes = []
    while len(codes) < RECOVERY_CODE_COUNT:
        raw = "".join(secrets.choice(RECOVERY_ALPHABET) for _index in range(10))
        code = f"{raw[:5]}-{raw[5:]}"
        if code not in codes:
            codes.append(code)
    device.recovery_codes.all().delete()
    RecoveryCode.objects.bulk_create(RecoveryCode(device=device, code_hash=_hash(code)) for code in codes)
    return codes


def recovery_codes_left(user: User) -> int:
    return RecoveryCode.objects.filter(device__user=user, used_at=None).count()


# ── Changes, each announced to the account owner ────────────────────────────


def _announce(user: User, kind: str, *, actor: User | None = None) -> None:
    """A security notice in the bell and by email, so a change nobody asked for gets noticed.

    `kind` is a notification message (`apps/notifications/messages.py`); the email says the
    same, in the account owner's language.
    """
    params = {"by": actor.display_name} if actor else {}
    notify([user], kind, actor=actor, level="warning", **params)
    with translation.override(user.language or settings.LANGUAGE_CODE):
        title, detail = render(kind, params)
        subject = _("PlanShift: %(title)s") % {"title": title}
        body = _(
            "Hi %(name)s,\n\n%(detail)s\n\n"
            "If this wasn't you or someone you asked, change your password and contact your manager straight away.\n\n"
            "— PlanShift"
        ) % {"name": user.display_name, "detail": detail}
    # Best-effort: the change already happened, a flaky mail relay must not undo or hide it.
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)


@transaction.atomic
def enable(user: User, secret: str, step: int) -> list[str]:
    """Save the confirmed secret and return fresh recovery codes, the only time they exist in clear."""
    # The step that confirmed the setup counts as used, so the same code can't also sign in.
    device = TOTPDevice.objects.create(user=user, secret=secret, last_used_step=step)
    codes = _replace_recovery_codes(device)
    _announce(user, "2fa.enabled")
    return codes


@transaction.atomic
def replace_recovery_codes(user: User) -> list[str]:
    codes = _replace_recovery_codes(TOTPDevice.objects.get(user=user))
    _announce(user, "2fa.recovery_codes")
    return codes


def disable(user: User, *, actor: User | None = None) -> bool:
    """Turn 2FA off (the recovery codes go with the device). False if it was already off."""
    deleted, _per_model = TOTPDevice.objects.filter(user=user).delete()
    if not deleted:
        return False
    _announce(user, "2fa.disabled" if actor is None else "2fa.reset", actor=actor)
    return True


# ── Checking a code ─────────────────────────────────────────────────────────


@transaction.atomic
def verify(user: User, code: str) -> Result:
    """Check an authenticator code or a recovery code, counting failures towards the lock.

    The row is locked for the check, so two requests racing with the same code
    can't both pass and failures can't be lost between them.
    """
    device = TOTPDevice.objects.select_for_update().filter(user=user).first()
    if device is None:
        return Result.INVALID

    now = timezone.now()
    if device.locked_until:
        if device.locked_until > now:
            return Result.LOCKED
        device.locked_until, device.failed_attempts = None, 0

    code = normalize(code)
    result = Result.INVALID
    if code.isdigit() and len(code) == totp.DIGITS:
        step = totp.matching_step(device.secret, code, after=device.last_used_step)
        if step is not None:
            device.last_used_step = step
            result = Result.CODE
    elif code and device.recovery_codes.filter(code_hash=_hash(code), used_at=None).update(used_at=now):
        result = Result.RECOVERY_CODE

    if result.ok:
        device.failed_attempts = 0
    else:
        device.failed_attempts += 1
        if device.failed_attempts >= MAX_FAILED_ATTEMPTS:
            device.locked_until = now + LOCK_DURATION
            result = Result.LOCKED
    device.save(update_fields=["last_used_step", "failed_attempts", "locked_until"])
    return result


# ── Read-only views of the state ────────────────────────────────────────────


def export_data(user: User) -> dict:
    """For the GDPR export: whether 2FA is on, never the secret or the codes."""
    device = TOTPDevice.objects.filter(user=user).first()
    return {
        "enabled": device is not None,
        "enabled_at": device.confirmed_at.isoformat() if device else None,
        "unused_recovery_codes": recovery_codes_left(user) if device else 0,
    }
