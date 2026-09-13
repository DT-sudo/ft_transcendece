"""Scheduling rules and writes. Views parse requests and render; the rules live here."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime

from django.core.exceptions import ValidationError
from django.db import models, transaction

from apps.accounts.models import User, UserRole
from apps.shell import first_form_error

from .forms import ShiftForm
from .models import Assignment, EmployeeUnavailability, Shift, ShiftStatus


def _check_position_match(shift: Shift, employee_ids: list[int]) -> None:
    valid = User.objects.filter(
        id__in=employee_ids,
        role=UserRole.EMPLOYEE,
        is_active=True,
        position_id=shift.position_id,
    ).count()
    if valid != len(employee_ids):
        raise ValidationError("Selected employees must match the shift position.")


def _check_capacity(shift: Shift, employee_ids: list[int]) -> None:
    if len(employee_ids) > shift.capacity:
        raise ValidationError("Cannot assign more employees than shift capacity.")


def _check_availability(shift: Shift, employee_ids: list[int]) -> None:
    if EmployeeUnavailability.objects.filter(employee_id__in=employee_ids, date=shift.date).exists():
        raise ValidationError(f"Employee is unavailable on {shift.date.isoformat()}.")


def _check_no_overlap(shift: Shift, employee_ids: list[int]) -> None:
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
    if conflict:
        other = conflict.shift
        raise ValidationError(
            f"Employee already assigned to: {other.position} "
            f"{other.start_time:%H:%M}–{other.end_time:%H:%M} ({other.date:%b %d})"
        )


def assign_employees_to_shift(shift: Shift, employee_ids: list[int]) -> None:
    """Replace the shift's assignments after running the four scheduling rules."""
    employee_ids = list(dict.fromkeys(employee_ids))
    if employee_ids:
        _check_position_match(shift, employee_ids)
        _check_capacity(shift, employee_ids)
        _check_availability(shift, employee_ids)
        _check_no_overlap(shift, employee_ids)
    Assignment.objects.filter(shift=shift).delete()
    Assignment.objects.bulk_create([Assignment(shift=shift, employee_id=eid) for eid in employee_ids])


def save_shift(shift: Shift, post_data) -> Shift:
    """Validate the posted form, then save the shift and its assignments in one transaction.

    Raises ValidationError with a user-facing message when either step rejects.
    """
    form = ShiftForm(post_data, instance=shift)
    if not form.is_valid():
        raise ValidationError(first_form_error(form, "Please check the form fields."))
    employee_ids = [int(value) for value in post_data.getlist("employee_ids") if value.isdigit()]

    with transaction.atomic():
        saved = form.save()
        assign_employees_to_shift(saved, employee_ids)
    return saved


def publish_shift(shift: Shift) -> None:
    shift.status = ShiftStatus.PUBLISHED
    shift.save(update_fields=["status"])


def publish_shifts_in_period(*, manager_id: int, start: date, end: date) -> int:
    return Shift.objects.filter(
        created_by_id=manager_id,
        status=ShiftStatus.DRAFT,
        date__gte=start,
        date__lte=end,
    ).update(status=ShiftStatus.PUBLISHED)


def shifts_for_manager(
    *,
    manager_id: int,
    start: date | None = None,
    end: date | None = None,
    position_id: int | None = None,
    status: str | None = None,
    understaffed_only: bool = False,
):
    qs = Shift.objects.filter(created_by_id=manager_id).select_related("position")
    if start:
        qs = qs.filter(date__gte=start)
    if end:
        qs = qs.filter(date__lte=end)
    if position_id:
        qs = qs.filter(position_id=position_id)
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
    )


# ── Search and analytics ────────────────────────────────────────────────────


def _hours(shift: Shift) -> float:
    duration = datetime.combine(shift.date, shift.end_time) - datetime.combine(shift.date, shift.start_time)
    return duration.total_seconds() / 3600


def shift_rows(*, manager_id: int, query: str = "", worker_id: int | None = None, **filters) -> list[dict]:
    """The manager's shifts with their workers, as plain dicts, for search and analytics.

    `filters` are those of `shifts_for_manager`. `query` matches the position or an
    assigned worker's name, case-insensitively.
    """
    shifts = shifts_for_manager(manager_id=manager_id, **filters).prefetch_related(
        models.Prefetch("assignments", queryset=Assignment.objects.select_related("employee"))
    )
    if worker_id:
        shifts = shifts.filter(assignments__employee_id=worker_id)

    rows = []
    for shift in shifts:
        workers = [
            {"id": a.employee_id, "name": a.employee.get_full_name() or a.employee.username}
            for a in shift.assignments.all()
        ]
        if query.lower() not in " ".join([shift.position.name, *(w["name"] for w in workers)]).lower():
            continue
        rows.append(
            {
                "id": shift.id,
                "date": shift.date.isoformat(),
                "start_time": shift.start_time.strftime("%H:%M"),
                "end_time": shift.end_time.strftime("%H:%M"),
                "position": shift.position.name,
                "status": shift.status,
                "capacity": shift.capacity,
                "hours": _hours(shift),
                "workers": workers,
            }
        )
    return rows


def shift_analytics(rows: list[dict], *, worker_id: int | None = None) -> dict:
    """KPIs and chart series over `shift_rows()` output.

    Shift counts describe whole shifts. Hours and workers count only the filtered
    worker, so a colleague on the same shift does not add to their numbers.
    """
    by_date: Counter[str] = Counter()
    by_position: Counter[str] = Counter()
    by_status = Counter(dict.fromkeys(ShiftStatus.values, 0))
    hours: Counter[int] = Counter()
    shift_count: Counter[int] = Counter()
    names: dict[int, str] = {}
    open_shifts = 0

    for row in rows:
        by_date[row["date"]] += 1
        by_position[row["position"]] += 1
        by_status[row["status"]] += 1
        open_shifts += len(row["workers"]) < row["capacity"]
        for worker in row["workers"]:
            if worker_id and worker["id"] != worker_id:
                continue
            hours[worker["id"]] += row["hours"]
            shift_count[worker["id"]] += 1
            names[worker["id"]] = worker["name"]

    ranked = sorted(hours, key=lambda wid: (hours[wid], shift_count[wid]), reverse=True)
    return {
        "kpis": {
            "shifts": len(rows),
            "hours": round(sum(hours.values()), 1),
            "workers": len(hours),
            "open_shifts": open_shifts,
        },
        "by_date": [{"date": day, "count": count} for day, count in sorted(by_date.items())],
        "by_position": [{"position": name, "count": count} for name, count in sorted(by_position.items())],
        "by_status": [{"status": status, "count": count} for status, count in by_status.items()],
        "top_workers": [
            {"worker": names[wid], "hours": round(hours[wid], 1), "shifts": shift_count[wid]} for wid in ranked[:10]
        ],
    }
