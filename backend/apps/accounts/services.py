from __future__ import annotations

from .models import MANAGER_POSITION_NAME, Position


def position_options(*, exclude_reserved: bool = False) -> list[dict]:
    """Every position as `{id, name}`, for the React selects.

    `exclude_reserved` drops the permanent "Manager" position: scheduling's own pickers
    (shift position, filters) are about job titles that get scheduled, not this promotion trigger.
    """
    positions = Position.objects.order_by("name")
    if exclude_reserved:
        positions = positions.exclude(name=MANAGER_POSITION_NAME)
    return [{"id": p.id, "name": p.name} for p in positions]
