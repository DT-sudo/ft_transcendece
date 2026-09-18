"""Who is told what when the schedule changes: the open pages that must re-read it, and the
notifications in the bell.

Employees only ever see published shifts, so a draft never notifies them. The shift details a
notification keeps are `shift_fields`: they outlive the shift itself.
"""

from __future__ import annotations

from collections.abc import Iterable

from apps.accounts.models import User
from apps.notifications.services import managers, notify
from apps.realtime.events import SHIFTS_CHANGED, notify_managers, push_to_user

from .models import Shift, ShiftStatus
from .services import shift_fields


def assigned_ids(shift: Shift) -> set[int]:
    return {assignment.employee_id for assignment in shift.assignments.all()}


def shifts_changed(employee_ids: Iterable[int] = ()) -> None:
    """Every manager's calendar, search and analytics re-read, and so do these employees' calendars."""
    notify_managers(SHIFTS_CHANGED)
    for employee_id in employee_ids:
        push_to_user(employee_id, SHIFTS_CHANGED)


def published(actor: User, shifts: list[Shift]) -> None:
    """One notification per assigned employee, however many of their shifts were published."""
    theirs: dict[int, list[dict]] = {}
    for shift in shifts:
        for employee_id in assigned_ids(shift):
            theirs.setdefault(employee_id, []).append(shift_fields(shift))
    shifts_changed(theirs)
    for employee_id, fields in theirs.items():
        notify([employee_id], "shift.assigned", actor=actor, shifts=fields)


def published_shift_edited(actor: User, shift: Shift, before_ids: set[int], before: dict) -> None:
    """Newly assigned, taken off, or still on it with a different day, time or position."""
    after_ids, after = assigned_ids(shift), shift_fields(shift)
    shifts_changed(before_ids | after_ids)
    notify(after_ids - before_ids, "shift.assigned", actor=actor, shifts=[after])
    notify(before_ids - after_ids, "shift.removed", actor=actor, level="warning", shift=before)
    if after != before:
        notify(after_ids & before_ids, "shift.changed", actor=actor, before=before, after=after)


def cancelled(actor: User, shifts: list[Shift]) -> None:
    """Deleted shifts. Their assignments must have been prefetched before the delete took them."""
    if not shifts:
        return
    told = {shift: assigned_ids(shift) for shift in shifts if shift.status == ShiftStatus.PUBLISHED}
    # Open pages re-read first, so the calendar has already changed when the notification arrives.
    shifts_changed(set().union(*told.values()))
    for shift, employee_ids in told.items():
        notify(employee_ids, "shift.cancelled", actor=actor, level="warning", shift=shift_fields(shift))


def staff_released(actor: User, name: str, shifts: list[Shift]) -> None:
    """Told to the managers: these upcoming shifts lost `name` and need restaffing."""
    notify(
        managers(),
        "shift.staff_released",
        actor=actor,
        level="warning",
        name=name,
        shifts=[shift_fields(shift) for shift in shifts],
    )
