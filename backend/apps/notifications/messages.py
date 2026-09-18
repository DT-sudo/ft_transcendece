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


def _day(iso: str) -> str:
    """"Mon 14 Sep", with the weekday and month names of the active language."""
    return date_format(date.fromisoformat(iso), "D j M")


def _shift_label(shift: dict) -> str:
    """One shift as `apps.scheduling.services.shift_fields` recorded it."""
    return _("%(position)s, %(day)s, %(start)s–%(end)s") % {
        "position": shift["position"],
        "day": _day(shift["date"]),
        "start": shift["start_time"],
        "end": shift["end_time"],
    }


def _shift_list(shifts: list[dict]) -> str:
    """The first few shifts as one line, with "and N more" standing in for the rest."""
    listed = "; ".join(_shift_label(shift) for shift in shifts[:MAX_LISTED_SHIFTS])
    extra = len(shifts) - MAX_LISTED_SHIFTS
    if extra > 0:
        listed += "; " + ngettext("and %(count)d more", "and %(count)d more", extra) % {"count": extra}
    return listed


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
    title = _("Your role was changed")
    values = {"by": p["by"], "role": _role(p)}
    if not p.get("was"):  # written before the old role was recorded
        return title, _("%(by)s made you %(role)s.") % values
    values["was"] = _role({"role": p["was"]})
    if p.get("position"):
        return title, _("%(by)s changed your role from %(was)s to %(role)s, position “%(position)s”.") % {
            **values,
            "position": p["position"],
        }
    return title, _("%(by)s changed your role from %(was)s to %(role)s.") % values


@_renders("account.position_changed")
def _position_changed(p):
    title = _("Your position was changed")
    if not p.get("was"):  # it had none: the old one was deleted, or written before it was recorded
        return title, _("%(by)s changed your position to “%(position)s”.") % p
    return title, _("%(by)s changed your position from “%(was)s” to “%(position)s”.") % p


@_renders("account.position_removed")
def _position_removed(p):
    return _("Your position was removed"), _("The position “%(position)s” no longer exists.") % p


@_renders("account.details_updated")
def _details_updated(p):
    return _("Your details were updated"), _("%(by)s changed your account.") % p


@_renders("account.password_reset")
def _password_reset(p):
    return _("Your password was reset"), _("%(by)s set a new password for your account.") % p


# ── Shifts, positions, availability ─────────────────────────────────────────


# Publishing a shift and adding someone to a published one read the same to the employee:
# shifts they now have.
@_renders("shift.assigned")
def _shifts_assigned(p):
    count = len(p["shifts"])
    if count == 1:
        title = _("New shift assigned")
    else:
        title = ngettext("%(count)d new shift assigned", "%(count)d new shifts assigned", count) % {"count": count}
    return title, _shift_list(p["shifts"])


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


@_renders("shift.released")
def _shift_released(p):
    """Told to the worker: upcoming shifts they are no longer on, and why."""
    count = len(p["shifts"])
    title = ngettext(
        "Taken off %(count)d upcoming shift", "Taken off %(count)d upcoming shifts", count
    ) % {"count": count}
    return title, _shift_list(p["shifts"])


@_renders("shift.staff_released")
def _shift_staff_released(p):
    """Told to the managers: an upcoming shift lost a worker, and needs restaffing."""
    count = len(p["shifts"])
    title = ngettext(
        "%(name)s came off %(count)d upcoming shift", "%(name)s came off %(count)d upcoming shifts", count
    ) % {"name": p["name"], "count": count}
    return title, _shift_list(p["shifts"])


@_renders("position.created")
def _position_created(p):
    return _("Position created"), p["name"]


@_renders("position.deleted")
def _position_deleted(p):
    return _("Position deleted"), p["name"]


@_renders("position.shifts_cancelled")
def _position_shifts_cancelled(p):
    """Told to the managers: the upcoming shifts that went with a deleted position."""
    count = len(p["shifts"])
    title = ngettext(
        "%(count)d upcoming shift of %(name)s deleted", "%(count)d upcoming shifts of %(name)s deleted", count
    ) % {"name": p["name"], "count": count}
    return title, _shift_list(p["shifts"])


@_renders("availability.changed")
def _availability_changed(p):
    values = {"name": p["name"], "day": _day(p["date"])}
    if p["unavailable"]:
        return _("Availability updated"), _("%(name)s is unavailable on %(day)s.") % values
    return _("Availability updated"), _("%(name)s is available again on %(day)s.") % values


# ── Errors ──────────────────────────────────────────────────────────────────


@_renders("error")
def _error(p):
    """An error the reader was shown as a toast, kept so it can be read again later."""
    return p.get("title") or _("Error"), p["text"]


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
