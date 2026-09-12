from __future__ import annotations

from datetime import date, datetime
from typing import Any

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Prefetch
from .models import Assignment, EmployeeUnavailability, Shift, ShiftStatus

def _normalize_employee_ids(employee_ids: list[int]) -> list[int]:
    return list(dict.fromkeys(employee_ids))


def _check_position_match(shift: Shift, employee_ids: list[int]) -> None:
    if not employee_ids:
        return

    User = get_user_model()
    valid_ids = set(
        User.objects.filter(
            id__in=employee_ids,
            role="employee",
            is_active=True,
            position_id=shift.position_id,
        ).values_list("id", flat=True)
    )
    if len(valid_ids) != len(employee_ids):
        raise ValidationError("Selected employees must match the shift position.")


def _check_capacity(shift: Shift, employee_ids: list[int]) -> None:
    if len(employee_ids) > shift.capacity:
        raise ValidationError("Cannot assign more employees than shift capacity.")


def _check_availability(shift: Shift, employee_ids: list[int]) -> None:
    if not employee_ids:
        return
    has_unavailable = EmployeeUnavailability.objects.filter(
        employee_id__in=employee_ids,
        date=shift.date,
    ).exists()
    if has_unavailable:
        raise ValidationError(f"Employee is unavailable on {shift.date.isoformat()}.")


def _check_no_overlap(shift: Shift, employee_ids: list[int]) -> None:
    if not employee_ids:
        return

    conflict = (
        Assignment.objects.filter(
            employee_id__in=employee_ids,
            shift__date=shift.date,
            shift__start_time__lt=shift.end_time,
            shift__end_time__gt=shift.start_time,
        )
        .exclude(shift_id=shift.id)
        .select_related("shift__position")
        .order_by("shift__start_time")
        .first()
    )
    if not conflict:
        return

    overlapping = conflict.shift
    start = overlapping.start_time.strftime("%H:%M")
    end = overlapping.end_time.strftime("%H:%M")
    day = overlapping.date.strftime("%b %d")
    raise ValidationError(f"Employee already assigned to: {overlapping.position} {start}–{end} ({day})")


def _sync_assignments(shift: Shift, employee_ids: list[int]) -> None:
    Assignment.objects.filter(shift=shift).delete()
    if not employee_ids:
        return
    Assignment.objects.bulk_create([Assignment(shift=shift, employee_id=eid) for eid in employee_ids])


def assign_employees_to_shift(shift: Shift, employee_ids: list[int]) -> None:
    employee_ids = _normalize_employee_ids(employee_ids)
    _check_position_match(shift, employee_ids)
    _check_capacity(shift, employee_ids)
    _check_availability(shift, employee_ids)
    _check_no_overlap(shift, employee_ids)
    _sync_assignments(shift, employee_ids)


def shifts_for_manager(
    *,
    manager_id: int,
    start: date,
    end: date,
    position_ids: list[int] | None = None,
    status: str | None = None,
    understaffed_only: bool = False,
):
    
    qs = Shift.objects.filter(created_by_id=manager_id, date__gte=start, date__lte=end).select_related("position")
    if position_ids:
        qs = qs.filter(position_id__in=position_ids)
    if status in (ShiftStatus.DRAFT, ShiftStatus.PUBLISHED):
        qs = qs.filter(status=status)
    if understaffed_only:
        qs = qs.annotate(assigned_total=models.Count("assignments")).filter(assigned_total__lt=models.F("capacity"))
    return qs

def shifts_for_employee(*, employee_id: int, start: date, end: date):
    
    return (
        Shift.objects.filter(
            assignments__employee_id=employee_id,
            date__gte=start,
            date__lte=end,
            status=ShiftStatus.PUBLISHED,
        )
        .select_related("position")
        .distinct()
        .order_by("date", "start_time")
    )


# ---------------------------------------------------------------------------
# Advanced search & analytics
#
# Both features read the same underlying shift data as the calendar, scoped
# to the manager exactly like `shifts_for_manager` above. Worker/manager/text
# filters are resolved in Python once assignments are prefetched, rather than
# through further queryset annotation: a manager's shift volume is small, and
# this sidesteps the row-multiplication issues that come from aggregating
# across the assignments join while also filtering on it.
# ---------------------------------------------------------------------------

def _employee_display_name(user) -> str:
    if user is None:
        return ""
    return (user.get_full_name() or "").strip() or user.username


def manager_scoped_shifts(
    *,
    manager_id: int,
    start: date | None = None,
    end: date | None = None,
    position_ids: list[int] | None = None,
    status: str | None = None,
):
    """Base queryset shared by search and analytics: a manager's own shifts
    with assignments (and their employees) prefetched."""
    qs = (
        Shift.objects.filter(created_by_id=manager_id)
        .select_related("position", "created_by")
        .prefetch_related(
            Prefetch("assignments", queryset=Assignment.objects.select_related("employee"))
        )
    )
    if start:
        qs = qs.filter(date__gte=start)
    if end:
        qs = qs.filter(date__lte=end)
    if position_ids:
        qs = qs.filter(position_id__in=position_ids)
    if status in (ShiftStatus.DRAFT, ShiftStatus.PUBLISHED):
        qs = qs.filter(status=status)
    return qs


def _shift_duration_hours(shift: Shift) -> float:
    delta = datetime.combine(date.min, shift.end_time) - datetime.combine(date.min, shift.start_time)
    return round(delta.total_seconds() / 3600, 2)


def _shift_row(shift: Shift) -> dict[str, Any]:
    """Flatten a (prefetched) shift into the shape search/analytics work with."""
    workers = [assignment.employee for assignment in shift.assignments.all()]
    return {
        "shift": shift,
        "worker_ids": [worker.id for worker in workers],
        "worker_names": [_employee_display_name(worker) for worker in workers],
        "manager_name": _employee_display_name(shift.created_by),
        "duration_hours": _shift_duration_hours(shift),
    }


def _row_matches(row: dict[str, Any], *, worker_ids, manager_ids, query) -> bool:
    if worker_ids and not (set(row["worker_ids"]) & set(worker_ids)):
        return False
    if manager_ids and row["shift"].created_by_id not in manager_ids:
        return False
    if query:
        haystack = " ".join(
            [row["shift"].position.name, row["manager_name"], *row["worker_names"]]
        ).lower()
        if query.lower() not in haystack:
            return False
    return True


_SEARCH_SORT_KEYS = {
    "date": lambda row: (row["shift"].date, row["shift"].start_time, row["shift"].id),
    "start_time": lambda row: (row["shift"].start_time, row["shift"].date, row["shift"].id),
    "worker": lambda row: (
        row["worker_names"][0].lower() if row["worker_names"] else "\uffff",
        row["shift"].date,
    ),
    "position": lambda row: (row["shift"].position.name.lower(), row["shift"].date),
}


def search_manager_shifts(
    *,
    manager_id: int,
    query: str = "",
    position_ids: list[int] | None = None,
    worker_ids: list[int] | None = None,
    manager_ids: list[int] | None = None,
    status: str | None = None,
    start: date | None = None,
    end: date | None = None,
    sort: str = "date",
    direction: str = "asc",
    page: int = 1,
    page_size: int = 25,
) -> dict[str, Any]:
    """Advanced search: free-text query plus explicit filters, sorting and
    pagination over a manager's shifts."""
    qs = manager_scoped_shifts(
        manager_id=manager_id, start=start, end=end, position_ids=position_ids, status=status
    ).order_by("date", "start_time")

    rows = [
        row
        for row in (_shift_row(shift) for shift in qs)
        if _row_matches(row, worker_ids=worker_ids, manager_ids=manager_ids, query=query)
    ]

    key_fn = _SEARCH_SORT_KEYS.get(sort, _SEARCH_SORT_KEYS["date"])
    rows.sort(key=key_fn, reverse=(direction == "desc"))

    total = len(rows)
    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    total_pages = max(1, -(-total // page_size))
    page = min(page, total_pages)
    start_index = (page - 1) * page_size

    return {
        "rows": rows[start_index : start_index + page_size],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def compute_shift_analytics(
    *,
    manager_id: int,
    start: date,
    end: date,
    position_ids: list[int] | None = None,
    worker_ids: list[int] | None = None,
    manager_ids: list[int] | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    """Aggregate KPI cards, chart series and top lists for the analytics
    dashboard. Shared by the server-rendered page and the JSON refresh
    endpoint so both report identical numbers."""
    qs = manager_scoped_shifts(
        manager_id=manager_id, start=start, end=end, position_ids=position_ids, status=status
    )
    rows = [
        row
        for row in (_shift_row(shift) for shift in qs)
        if _row_matches(row, worker_ids=worker_ids, manager_ids=manager_ids, query="")
    ]

    total_hours = 0.0
    open_shifts = 0
    workers_seen: set[int] = set()

    by_date: dict[str, int] = {}
    by_position: dict[str, int] = {}
    by_status: dict[str, int] = {"draft": 0, "published": 0}
    hours_by_worker: dict[str, float] = {}
    shifts_by_worker: dict[str, int] = {}
    shifts_by_manager: dict[str, int] = {}

    worker_filter = set(worker_ids) if worker_ids else None

    for row in rows:
        shift = row["shift"]
        iso = shift.date.isoformat()
        position_name = shift.position.name
        assigned_count = len(row["worker_ids"])

        # When a worker filter is active, per-worker figures (hours, the
        # "Workers" KPI, the hours/top-workers lists) must isolate the
        # selected worker(s) — a shift with a colleague also assigned should
        # not pull that colleague's hours or headcount into the numbers.
        # Shift-level figures (position/date/status breakdowns, capacity)
        # still describe the whole shift regardless of who's being filtered.
        relevant_workers = [
            (worker_id, worker_name)
            for worker_id, worker_name in zip(row["worker_ids"], row["worker_names"])
            if worker_filter is None or worker_id in worker_filter
        ]

        total_hours += row["duration_hours"] * len(relevant_workers)
        if assigned_count < shift.capacity:
            open_shifts += 1

        by_date[iso] = by_date.get(iso, 0) + 1
        by_position[position_name] = by_position.get(position_name, 0) + 1
        by_status[shift.status] = by_status.get(shift.status, 0) + 1
        shifts_by_manager[row["manager_name"]] = shifts_by_manager.get(row["manager_name"], 0) + 1

        for worker_id, worker_name in relevant_workers:
            workers_seen.add(worker_id)
            hours_by_worker[worker_name] = hours_by_worker.get(worker_name, 0.0) + row["duration_hours"]
            shifts_by_worker[worker_name] = shifts_by_worker.get(worker_name, 0) + 1

    hours_per_worker = sorted(
        ({"worker": name, "hours": round(hours, 2)} for name, hours in hours_by_worker.items()),
        key=lambda item: item["hours"],
        reverse=True,
    )[:10]
    top_workers = sorted(
        (
            {
                "worker": name,
                "shifts": shifts_by_worker[name],
                "hours": round(hours_by_worker.get(name, 0.0), 2),
            }
            for name in shifts_by_worker
        ),
        key=lambda item: (item["hours"], item["shifts"]),
        reverse=True,
    )[:5]
    top_managers = sorted(
        ({"manager": name, "shifts": count} for name, count in shifts_by_manager.items()),
        key=lambda item: item["shifts"],
        reverse=True,
    )[:5]
    top_positions = sorted(
        ({"position": name, "shifts": count} for name, count in by_position.items()),
        key=lambda item: item["shifts"],
        reverse=True,
    )[:5]

    return {
        "kpis": {
            "total_shifts": len(rows),
            "total_hours": round(total_hours, 1),
            "workers": len(workers_seen),
            "open_shifts": open_shifts,
        },
        "charts": {
            "shifts_over_time": [
                {"date": iso, "count": count} for iso, count in sorted(by_date.items())
            ],
            "shifts_by_position": [
                {"position": name, "count": count}
                for name, count in sorted(by_position.items(), key=lambda item: item[0].lower())
            ],
            "status_distribution": [
                {"status": key, "count": value} for key, value in by_status.items()
            ],
            "hours_per_worker": hours_per_worker,
        },
        "top": {
            "workers": top_workers,
            "managers": top_managers,
            "positions": top_positions,
        },
        "rows": rows,
    }
