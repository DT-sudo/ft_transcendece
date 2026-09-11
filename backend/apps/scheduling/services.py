"""Scheduling rules and writes. Views parse requests and render; the rules live here."""

from __future__ import annotations

from datetime import date

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
    shift.save(update_fields=["status", "updated_at"])


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
    )
