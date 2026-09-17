"""What each kind of notification says, written out in the reader's language when it is read.

A notification stores its `kind` and the facts behind it (`params`), not finished
sentences, so the same row reads in Czech for one person and in Arabic for another,
and follows a reader who switches language.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from django.utils.formats import date_format
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

RENDERERS: dict[str, Callable[[dict], tuple[str, str]]] = {}
MAX_LISTED_SHIFTS = 3


def _renders(kind: str):
    def register(function):
        RENDERERS[kind] = function
        return function

    return register


def render(kind: str, params: dict) -> tuple[str, str]:
    """(title, description) in the active language."""
    return RENDERERS[kind](params)


def shift_params(shift) -> dict:
    """The facts a notification keeps about a shift; they outlive the shift itself."""
    return {
        "position": shift.position.name,
        "date": shift.date.isoformat(),
        "start": f"{shift.start_time:%H:%M}",
        "end": f"{shift.end_time:%H:%M}",
    }


def _day(iso: str) -> str:
    """"Mon 14 Sep", with the weekday and month names of the active language."""
    return date_format(date.fromisoformat(iso), "D j M")


def _shift_label(params: dict) -> str:
    return _("%(position)s, %(day)s, %(start)s–%(end)s") % {**params, "day": _day(params["date"])}


def _role(params: dict) -> str:
    from apps.accounts.models import UserRole

    return str(UserRole(params["role"]).label)


# ── Accounts ────────────────────────────────────────────────────────────────


@_renders("account.added")
def _account_added(p):
    return _("%(role)s added") % {"role": _role(p)}, p["name"]


@_renders("account.updated")
def _account_updated(p):
    return _("%(role)s updated") % {"role": _role(p)}, p["name"]


@_renders("account.deleted")
def _account_deleted(p):
    return _("%(role)s deleted") % {"role": _role(p)}, p["name"]


@_renders("account.role_changed")
def _role_changed(p):
    return _("Your role was changed"), _("%(by)s made you %(role)s.") % {"by": p["by"], "role": _role(p)}


@_renders("account.details_updated")
def _details_updated(p):
    return _("Your details were updated"), _("%(by)s changed your account.") % p


@_renders("account.password_reset")
def _password_reset(p):
    return _("Your password was reset"), _("%(by)s set a new password for your account.") % p


# ── Shifts, positions, availability ─────────────────────────────────────────


@_renders("shift.published")
def _shifts_published(p):
    shifts = p["shifts"]
    count = len(shifts)
    if count == 1:
        title = _("New shift published")
    else:
        title = ngettext("%(count)d new shift published", "%(count)d new shifts published", count) % {"count": count}
    description = "; ".join(_shift_label(shift) for shift in shifts[:MAX_LISTED_SHIFTS])
    extra = count - MAX_LISTED_SHIFTS
    if extra > 0:
        description += "; " + ngettext("and %(count)d more", "and %(count)d more", extra) % {"count": extra}
    return title, description


@_renders("shift.assigned")
def _shift_assigned(p):
    return _("New shift assigned"), _shift_label(p["shift"])


@_renders("shift.removed")
def _shift_removed(p):
    return _("Removed from a shift"), _shift_label(p["shift"])


@_renders("shift.changed")
def _shift_changed(p):
    return _("Shift changed"), _("%(before)s is now %(after)s") % {
        "before": _shift_label(p["before"]),
        "after": _shift_label(p["after"]),
    }


@_renders("shift.cancelled")
def _shift_cancelled(p):
    return _("Shift cancelled"), _shift_label(p["shift"])


@_renders("position.created")
def _position_created(p):
    return _("Position created"), p["name"]


@_renders("position.deleted")
def _position_deleted(p):
    return _("Position deleted"), p["name"]


@_renders("availability.changed")
def _availability_changed(p):
    values = {"name": p["name"], "day": _day(p["date"])}
    if p["unavailable"]:
        return _("Availability updated"), _("%(name)s is unavailable on %(day)s.") % values
    return _("Availability updated"), _("%(name)s is available again on %(day)s.") % values


# ── Friends ─────────────────────────────────────────────────────────────────


@_renders("friend.requested")
def _friend_requested(p):
    return _("New friend request"), _("%(name)s wants to add you as a friend.") % p


@_renders("friend.accepted")
def _friend_accepted(p):
    return _("Friend request accepted"), _("%(name)s accepted your friend request.") % p


@_renders("friend.removed")
def _friend_removed(p):
    return _("Friend removed"), _("%(name)s removed you from their friends.") % p


# ── Two-factor authentication ───────────────────────────────────────────────


@_renders("2fa.enabled")
def _two_factor_enabled(p):
    return (
        _("Two-factor authentication turned on"),
        _("Signing in to your account now also takes a code from your authenticator app."),
    )


@_renders("2fa.recovery_codes")
def _two_factor_codes(p):
    return (
        _("New recovery codes created"),
        _("New recovery codes were created for your account. The old ones no longer work."),
    )


@_renders("2fa.disabled")
def _two_factor_disabled(p):
    return _("Two-factor authentication turned off"), _("Signing in to your account no longer takes a code.")


@_renders("2fa.reset")
def _two_factor_reset(p):
    return (
        _("Two-factor authentication reset"),
        _("%(by)s turned off two-factor authentication for your account. Turn it on again in Account settings.")
        % p,
    )
