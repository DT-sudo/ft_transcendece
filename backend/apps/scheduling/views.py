"""Manager calendar and shift/position writes; employee calendar and availability."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Prefetch
from django.db.models.deletion import ProtectedError
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from apps.accounts.views import employee_required, manager_required
from apps.accounts.models import User, UserRole
from apps.frontend.shell import first_form_error, flash_redirect, render_app
from apps.realtime.events import notify_managers

from .forms import PositionForm
from .models import Assignment, EmployeeUnavailability, Position, Shift
from .services import (
    publish_shift,
    publish_shifts_in_period,
    save_shift,
    shifts_for_employee,
    shifts_for_manager,
)

# ── Periods ─────────────────────────────────────────────────────────────────


def _parse_date(value: str | None, default: date | None) -> date | None:
    """Parse YYYY-MM-DD, return default if missing or invalid."""
    try:
        return datetime.strptime((value or "").strip(), "%Y-%m-%d").date()
    except ValueError:
        return default


def _month_bounds(anchor: date) -> tuple[date, date]:
    start = anchor.replace(day=1)
    next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    return start, next_month - timedelta(days=1)


@dataclass(frozen=True)
class Period:
    view: str
    anchor: date
    start: date
    end: date
    label: str


def _period(view_raw: str | None, anchor: date) -> Period:
    if (view_raw or "").lower() == "month":
        start, end = _month_bounds(anchor)
        return Period("month", anchor, start, end, anchor.strftime("%B %Y"))

    start = anchor - timedelta(days=anchor.weekday())
    end = start + timedelta(days=6)
    if (start.month, start.year) == (end.month, end.year):
        label = f"{start:%d}. - {end:%d}. {start:%b}"
    else:
        label = f"{start:%d}. {start:%b} - {end:%d}. {end:%b}"
    return Period("week", anchor, start, end, label)


# ── Manager calendar ────────────────────────────────────────────────────────


def _manager_shift_or_404(request: HttpRequest, shift_id: int) -> Shift:
    return get_object_or_404(Shift, pk=shift_id, created_by=request.user)


def _calendar_url(request: HttpRequest, shift: Shift) -> str:
    """The manager calendar, in the view the form was opened from, showing the shift's date."""
    view = request.POST.get("return_view", "week")
    return f"{reverse('manager_shifts')}?view={view if view in {'week', 'month'} else 'week'}&date={shift.date.isoformat()}"


def _shift_payload(shift_qs) -> list[dict]:
    shifts = shift_qs.annotate(assigned_count=Count("assignments")).prefetch_related(
        Prefetch("assignments", queryset=Assignment.objects.only("employee_id"), to_attr="prefetched_assignments")
    )
    return [
        {
            "id": s.id,
            "date": s.date.isoformat(),
            "start_time": s.start_time.strftime("%H:%M"),
            "end_time": s.end_time.strftime("%H:%M"),
            "position": s.position.name,
            "position_id": s.position_id,
            "capacity": s.capacity,
            "assigned_count": s.assigned_count,
            "assigned_employee_ids": [a.employee_id for a in s.prefetched_assignments],
            "status": s.status,
            "is_past": s.is_past,
        }
        for s in shifts
    ]


def _unavailability_payload(*, since: date) -> dict[str, list[str]]:
    """Unavailable days per active employee from `since` on, keyed by employee id."""
    days: dict[str, list[str]] = {}
    rows = EmployeeUnavailability.objects.filter(date__gte=since, employee__is_active=True).values_list(
        "employee_id", "date"
    )
    for employee_id, day in rows:
        days.setdefault(str(employee_id), []).append(day.isoformat())
    return days


@manager_required
@require_GET
def manager_shifts(request: HttpRequest) -> HttpResponse:
    today = timezone.localdate()
    period = _period(request.GET.get("view"), _parse_date(request.GET.get("date"), today))

    selected_positions = [int(p) for p in request.GET.getlist("positions") if p.isdigit()]
    status = (request.GET.get("status") or "").lower()
    understaffed = request.GET.get("show") == "understaffed"

    shift_qs = shifts_for_manager(
        manager_id=request.user.id,
        start=period.start,
        end=period.end,
        position_ids=selected_positions or None,
        status=status or None,
        understaffed_only=understaffed,
    )
    employees = (
        User.objects.filter(role=UserRole.EMPLOYEE, is_active=True)
        .select_related("position")
        .order_by("last_name", "first_name", "username")
    )

    return render_app(
        request,
        page="manager-shifts",
        title="Shift Management",
        description="PlanShift - Manage employee shifts",
        body_class="manager-shifts-page",
        nav_active="manager_shifts",
        data={
            "view": period.view,
            "anchor": period.anchor.isoformat(),
            "start": period.start.isoformat(),
            "end": period.end.isoformat(),
            "today": today.isoformat(),
            "periodLabel": period.label,
            "positions": [{"id": p.id, "name": p.name} for p in Position.objects.order_by("name")],
            "employees": [
                {
                    "id": e.id,
                    "name": e.get_full_name() or e.username,
                    "position_id": e.position_id,
                    "position": e.position.name if e.position else "",
                }
                for e in employees
            ],
            # Not bounded by the visible period: the shift form can be set to any upcoming date.
            "unavailability": _unavailability_payload(since=min(period.start, today)),
            "shifts": _shift_payload(shift_qs),
            "filters": {"positions": selected_positions, "status": status, "understaffed": understaffed},
            "urls": {
                "create": reverse("create_shift"),
                "update": reverse("update_shift", args=[0]),
                "delete": reverse("delete_shift", args=[0]),
                "publish": reverse("publish_shift", args=[0]),
                "publishAll": reverse("publish_all_shifts"),
            },
        },
    )


@manager_required
@require_POST
def save_shift_view(request: HttpRequest, shift_id: int | None = None) -> HttpResponse:
    is_update = shift_id is not None
    shift = _manager_shift_or_404(request, shift_id) if is_update else Shift(created_by=request.user)
    try:
        saved = save_shift(shift, request.POST)
    except ValidationError as exc:
        return flash_redirect(request, messages.ERROR, " ".join(exc.messages), "manager_shifts")
    return flash_redirect(
        request, messages.SUCCESS, "Shift updated." if is_update else "Shift created.", _calendar_url(request, saved)
    )


@manager_required
@require_POST
def delete_shift(request: HttpRequest, shift_id: int) -> HttpResponse:
    _manager_shift_or_404(request, shift_id).delete()
    return flash_redirect(request, messages.SUCCESS, "Shift deleted.", "manager_shifts")


@manager_required
@require_POST
def publish_shift_view(request: HttpRequest, shift_id: int) -> HttpResponse:
    shift = _manager_shift_or_404(request, shift_id)
    if publish_shift(shift):
        return flash_redirect(request, messages.SUCCESS, "Shift published.", _calendar_url(request, shift))
    return flash_redirect(request, messages.INFO, "Shift is already published.", _calendar_url(request, shift))


@manager_required
@require_POST
def publish_all_shifts(request: HttpRequest) -> HttpResponse:
    """Publish all draft shifts in the visible date range."""
    period = _period(request.POST.get("view"), _parse_date(request.POST.get("date"), timezone.localdate()))
    count = publish_shifts_in_period(manager_id=request.user.id, start=period.start, end=period.end)
    if count:
        return flash_redirect(request, messages.SUCCESS, f"Published {count} shift{'s' if count != 1 else ''}.", "manager_shifts")
    return flash_redirect(request, messages.INFO, "No draft shifts to publish.", "manager_shifts")


# ── Positions ───────────────────────────────────────────────────────────────


@manager_required
@require_POST
def position_create(request: HttpRequest) -> HttpResponse:
    form = PositionForm(request.POST)
    if not form.is_valid():
        return flash_redirect(request, messages.ERROR, first_form_error(form, "Could not create position."), "manager_employees")
    return flash_redirect(request, messages.SUCCESS, f"Position created: {form.save().name}.", "manager_employees")


@manager_required
@require_POST
def position_delete(request: HttpRequest, position_id: int) -> HttpResponse:
    position = get_object_or_404(Position, pk=position_id)
    try:
        position.delete()
    except ProtectedError:
        return flash_redirect(
            request, messages.ERROR, "Cannot delete position: it is referenced by existing data.", "manager_employees"
        )
    return flash_redirect(request, messages.SUCCESS, f"Position deleted: {position.name}.", "manager_employees")


# ── Employee calendar ───────────────────────────────────────────────────────


@employee_required
@require_GET
def employee_shifts_view(request: HttpRequest) -> HttpResponse:
    today = timezone.localdate()
    anchor = _parse_date(request.GET.get("date"), today)
    start, end = _month_bounds(anchor)

    unavailable = EmployeeUnavailability.objects.filter(
        employee_id=request.user.id, date__gte=start, date__lte=end
    ).values_list("date", flat=True)

    return render_app(
        request,
        page="employee-shifts",
        title="My Shifts",
        description="Employee shift calendar",
        nav_active="employee_shifts",
        data={
            "anchor": anchor.isoformat(),
            "start": start.isoformat(),
            "end": end.isoformat(),
            "today": today.isoformat(),
            "periodLabel": anchor.strftime("%B %Y"),
            "shifts": [
                {
                    "id": s.id,
                    "date": s.date.isoformat(),
                    "start_time": s.start_time.strftime("%H:%M"),
                    "end_time": s.end_time.strftime("%H:%M"),
                    "position": s.position.name,
                    "is_past": s.is_past,
                }
                for s in shifts_for_employee(employee_id=request.user.id, start=start, end=end)
            ],
            "unavailable": [day.isoformat() for day in unavailable],
            "urls": {"toggleUnavailability": reverse("employee_unavailability_toggle")},
        },
    )


@employee_required
@require_POST
def employee_unavailability_toggle(request: HttpRequest) -> JsonResponse:
    day = _parse_date(request.POST.get("date"), None)
    if day is None:
        return JsonResponse({"ok": False, "error": "Enter a valid date."}, status=400)
    if day <= timezone.localdate():
        return JsonResponse(
            {"ok": False, "error": "Only dates from tomorrow onwards can be marked as unavailable."}, status=400
        )
    if Assignment.objects.filter(employee_id=request.user.id, shift__date=day).exists():
        return JsonResponse({"ok": False, "error": "You have a shift assigned on this day."}, status=400)

    existing = EmployeeUnavailability.objects.filter(employee_id=request.user.id, date=day)
    unavailable = not existing.exists()
    if unavailable:
        EmployeeUnavailability.objects.create(employee_id=request.user.id, date=day)
    else:
        existing.delete()

    # Open manager calendars update immediately instead of on their next reload.
    notify_managers(
        {
            "type": "unavailability.changed",
            "employeeId": request.user.id,
            "employeeName": request.user.get_full_name() or request.user.username,
            "date": day.isoformat(),
            "unavailable": unavailable,
        }
    )
    return JsonResponse({"ok": True, "date": day.isoformat(), "unavailable": unavailable})
