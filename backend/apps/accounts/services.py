from __future__ import annotations

from django.db import transaction

from apps.notifications.services import managers, notify
from apps.scheduling import notices
from apps.scheduling.models import ShiftStatus
from apps.scheduling.services import delete_upcoming_shifts_of_position, release_from_future_shifts, shift_fields

from .models import MANAGER_POSITION_NAME, Position, User


def position_options(*, exclude_reserved: bool = False) -> list[dict]:
    """Every position as `{id, name}`, for the React selects.

    `exclude_reserved` drops the permanent "Manager" position: scheduling's own pickers
    (shift position, filters) are about job titles that get scheduled, not this promotion trigger.
    """
    positions = Position.objects.order_by("name")
    if exclude_reserved:
        positions = positions.exclude(name=MANAGER_POSITION_NAME)
    return [{"id": p.id, "name": p.name} for p in positions]


def release_from_upcoming(account: User, *, actor: User | None, tell_account: bool = True) -> None:
    """Take `account` off the shifts it can no longer work, and tell everyone concerned.

    Its started shifts are left alone - they record who was actually there. Called when an
    account's role or position changed, or just before it is deleted: exactly when a future
    booking stops being valid. `tell_account=False` is for the deletion, which it won't read.
    """
    released = release_from_future_shifts(account.pk)
    if not released:
        return
    notices.shifts_changed([account.pk])

    # Drafts were never shown to the worker, so only published shifts are news to them.
    published = [shift_fields(shift) for shift in released if shift.status == ShiftStatus.PUBLISHED]
    if published and tell_account:
        notify([account], "shift.released", actor=actor, level="warning", shifts=published)
    notices.staff_released(actor, account.display_name, released)


def delete_position(position: Position, *, actor: User) -> None:
    """Delete a position with its upcoming shifts, and tell everyone concerned.

    Its started shifts stay on the schedule under its name. The employees who held it are
    left without a position until they are given another one.
    """
    holders = list(position.employees.values_list("pk", flat=True))
    with transaction.atomic():
        cancelled = delete_upcoming_shifts_of_position(position.pk)
        position.delete()

    notices.cancelled(actor, cancelled)
    notify(holders, "account.position_removed", actor=actor, level="warning", position=position.name)
    notify(managers(), "position.deleted", actor=actor, level="warning", name=position.name)
    if cancelled:
        notify(
            managers(),
            "position.shifts_cancelled",
            actor=actor,
            level="warning",
            name=position.name,
            shifts=[shift_fields(shift) for shift in cancelled],
        )
