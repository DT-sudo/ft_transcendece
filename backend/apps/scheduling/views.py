"""Manager calendar and shift/position writes; employee calendar and availability."""

from __future__ import annotations

import csv
from datetime import date, datetime, timedelta

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models.deletion import ProtectedError
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from apps.accounts.views import employee_required, manager_required
from apps.accounts.models import User, UserRole
from apps.notifications.services import managers, notify
from apps.shell import first_form_error, flash_redirect, render_app
from apps.realtime.events import notify_managers, push_to_user

from .forms import PositionForm
from .models import Assignment, EmployeeUnavailability, Position, Shift, ShiftStatus
from .services import (
    position_options,
    publish_shift,
    publish_shifts_in_period,
    save_shift,
    shift_analytics,
    shift_fields,
    shift_rows,
    shifts_for_employee,
    shifts_for_manager,
)

# Open calendars and analytics dashboards re-fetch their data when a shift is written.
SHIFTS_CHANGED = {"type": "shifts.changed"}

# ── Query parameters and periods ────────────────────────────────────────────


def _parse_date(value: str | None, default: date | None) -> date | None:
    """Parse YYYY-MM-DD, return default if missing or invalid."""
    try:
        return datetime.strptime((value or "").strip(), "%Y-%m-%d").date()
    except ValueError:
        return default


def _parse_id(value: str | None) -> int | None:
    return int(value) if value and value.isdigit() else None


def _month_bounds(anchor: date) -> tuple[date, date]:
    start = anchor.replace(day=1)
    next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    return start, next_month - timedelta(days=1)


CALENDAR_VIEWS = ("month", "week")


def _calendar_view(request: HttpRequest) -> str:
    """"month" or "week": the one asked for, else the manager's last choice.

    Kept in the session, so the redirect after a save or delete lands on the same view.
    """
    view = request.GET.get("view") or request.POST.get("view")
    if view in CALENDAR_VIEWS:
        request.session["calendar_view"] = view
        return view
    return request.session.get("calendar_view", "month")


def _period(view: str, anchor: date) -> tuple[date, date]:
    """The visible days: the anchor's month, or its Monday-to-Sunday week."""
    if view == "week":
        start = anchor - timedelta(days=anchor.weekday())
        return start, start + timedelta(days=6)
    return _month_bounds(anchor)


# ── Manager calendar ────────────────────────────────────────────────────────


def _manager_shift_or_404(request: HttpRequest, shift_id: int) -> Shift:
    return get_object_or_404(Shift, pk=shift_id, created_by=request.user)


def _active_employees():
    return User.objects.filter(role=UserRole.EMPLOYEE, is_active=True).order_by("last_name", "first_name", "username")


def _calendar_url(shift: Shift) -> str:
    """The manager calendar showing the shift's month."""
    return f"{reverse('manager_shifts')}?date={shift.date.isoformat()}"


def _shift_payload(shift_qs) -> list[dict]:
    return [
        {
            "id": s.id,
            **shift_fields(s),
            "position_id": s.position_id,
            "capacity": s.capacity,
            "assigned_employee_ids": [a.employee_id for a in s.assignments.all()],
            "status": s.status,
            "is_past": s.is_past,
            "version": s.version,
        }
        for s in shift_qs.prefetch_related("assignments")
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
    anchor = _parse_date(request.GET.get("date"), today)
    view = _calendar_view(request)
    start, end = _period(view, anchor)

    position_id = _parse_id(request.GET.get("position"))
    status = (request.GET.get("status") or "").lower()
    understaffed = request.GET.get("show") == "understaffed"

    shift_qs = shifts_for_manager(
        manager_id=request.user.id,
        start=start,
        end=end,
        position_id=position_id,
        status=status or None,
        understaffed_only=understaffed,
    )
    employees = _active_employees().select_related("position")

    return render_app(
        request,
        page="manager-shifts",
        title="Shift Management",
        nav_active="manager_shifts",
        data={
            "view": view,
            "anchor": anchor.isoformat(),
            "start": start.isoformat(),
            "end": end.isoformat(),
            "today": today.isoformat(),
            "positions": position_options(),
            "employees": [
                {
                    "id": e.id,
                    "name": e.display_name,
                    "position_id": e.position_id,
                    "position": e.position.name if e.position else "",
                }
                for e in employees
            ],
            # Not bounded by the visible period: the shift form can be set to any upcoming date.
            "unavailability": _unavailability_payload(since=min(start, today)),
            "shifts": _shift_payload(shift_qs),
            "filters": {"position": position_id or "", "status": status, "understaffed": understaffed},
            "urls": {
                "create": reverse("create_shift"),
                "update": reverse("update_shift", args=[0]),
                "delete": reverse("delete_shift", args=[0]),
                "publish": reverse("publish_shift", args=[0]),
                "publishAll": reverse("publish_all_shifts"),
            },
        },
    )


# Employees only see published shifts, so drafts never notify them.


def _shift_label(shift: Shift) -> str:
    return f"{shift.position.name}, {shift.date:%a %b %d}, {shift.start_time:%H:%M}–{shift.end_time:%H:%M}"


def _assigned_ids(shift: Shift) -> set[int]:
    return {assignment.employee_id for assignment in shift.assignments.all()}


def _shifts_changed(employee_ids=()) -> None:
    """Open manager pages re-fetch, and so do the calendars of employees whose published shifts changed."""
    notify_managers(SHIFTS_CHANGED)
    for employee_id in employee_ids:
        push_to_user(employee_id, SHIFTS_CHANGED)


def _notify_published(actor: User, shifts: list[Shift]) -> None:
    """Refresh open calendars, then one notification per assigned employee, however many of their shifts were published."""
    labels: dict[int, list[str]] = {}
    for shift in shifts:
        for employee_id in _assigned_ids(shift):
            labels.setdefault(employee_id, []).append(_shift_label(shift))
    _shifts_changed(labels)
    for employee_id, theirs in labels.items():
        title = "New shift published" if len(theirs) == 1 else f"{len(theirs)} new shifts published"
        more = f"; and {len(theirs) - 3} more" if len(theirs) > 3 else ""
        notify([employee_id], title, "; ".join(theirs[:3]) + more, actor=actor)


def _notify_published_shift_edited(actor: User, shift: Shift, before_ids: set[int], before_label: str) -> None:
    after_ids, label = _assigned_ids(shift), _shift_label(shift)
    _shifts_changed(before_ids | after_ids)
    notify(after_ids - before_ids, "New shift assigned", label, actor=actor)
    notify(before_ids - after_ids, "Removed from a shift", before_label, actor=actor, level="warning")
    if label != before_label:
        notify(after_ids & before_ids, "Shift changed", f"{before_label} is now {label}", actor=actor)


@manager_required
@require_POST
def save_shift_view(request: HttpRequest, shift_id: int | None = None) -> HttpResponse:
    is_update = shift_id is not None
    shift = _manager_shift_or_404(request, shift_id) if is_update else Shift(created_by=request.user)
    # Read before saving: validating the form writes the posted values onto `shift`.
    was_published = shift.status == ShiftStatus.PUBLISHED
    before_ids, before_label = (_assigned_ids(shift), _shift_label(shift)) if was_published else (set(), "")
    try:
        saved = save_shift(shift, request.POST)
    except ValidationError as exc:
        return flash_redirect(request, messages.ERROR, " ".join(exc.messages), "manager_shifts")
    if was_published:
        _notify_published_shift_edited(request.user, saved, before_ids, before_label)
    else:
        _shifts_changed()
    return flash_redirect(
        request, messages.SUCCESS, "Shift updated." if is_update else "Shift created.", _calendar_url(saved)
    )


@manager_required
@require_POST
def delete_shift(request: HttpRequest, shift_id: int) -> HttpResponse:
    shift = _manager_shift_or_404(request, shift_id)
    employee_ids = _assigned_ids(shift) if shift.status == ShiftStatus.PUBLISHED else set()
    label = _shift_label(shift)
    shift.delete()
    _shifts_changed(employee_ids)
    notify(employee_ids, "Shift cancelled", label, actor=request.user, level="warning")
    return flash_redirect(request, messages.SUCCESS, "Shift deleted.", "manager_shifts")


@manager_required
@require_POST
def publish_shift_view(request: HttpRequest, shift_id: int) -> HttpResponse:
    shift = _manager_shift_or_404(request, shift_id)
    was_draft = shift.status == ShiftStatus.DRAFT
    publish_shift(shift)
    if was_draft:
        _notify_published(request.user, [shift])
    return flash_redirect(request, messages.SUCCESS, "Shift published.", _calendar_url(shift))


@manager_required
@require_POST
def publish_all_shifts(request: HttpRequest) -> HttpResponse:
    """Publish all draft shifts in the visible month or week."""
    start, end = _period(_calendar_view(request), _parse_date(request.POST.get("date"), timezone.localdate()))
    published = publish_shifts_in_period(manager_id=request.user.id, start=start, end=end)
    if published:
        _notify_published(request.user, published)
        count = len(published)
        return flash_redirect(request, messages.SUCCESS, f"Published {count} shift{'s' if count != 1 else ''}.", "manager_shifts")
    return flash_redirect(request, messages.INFO, "No draft shifts to publish.", "manager_shifts")


# ── Positions ───────────────────────────────────────────────────────────────


@manager_required
@require_POST
def position_create(request: HttpRequest) -> HttpResponse:
    form = PositionForm(request.POST)
    if not form.is_valid():
        return flash_redirect(request, messages.ERROR, first_form_error(form, "Could not create position."), "manager_employees")
    position = form.save()
    notify(managers(), "Position created", position.name, actor=request.user)
    return flash_redirect(request, messages.SUCCESS, f"Position created: {position.name}.", "manager_employees")


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
    notify(managers(), "Position deleted", position.name, actor=request.user, level="warning")
    return flash_redirect(request, messages.SUCCESS, f"Position deleted: {position.name}.", "manager_employees")


# ── Search and analytics ────────────────────────────────────────────────────

FILTER_PARAMS = ("q", "position", "worker", "status", "date_from", "date_to")
SEARCH_PAGE_SIZE = 25
SEARCH_SORTS = {
    "date": lambda row: (row["date"], row["start_time"]),
    "time": lambda row: (row["start_time"], row["date"]),
    "position": lambda row: (row["position"].lower(), row["date"]),
    # Unassigned shifts sort after every name.
    "worker": lambda row: (row["workers"][0]["name"].lower() if row["workers"] else "￿", row["date"]),
}
ANALYTICS_DEFAULT_DAYS = 30


def _shift_filters(request: HttpRequest) -> dict:
    """The filter bar shared by search and analytics, as `shift_rows()` arguments."""
    return {
        "position_id": _parse_id(request.GET.get("position")),
        "worker_id": _parse_id(request.GET.get("worker")),
        "status": (request.GET.get("status") or "").lower() or None,
        "start": _parse_date(request.GET.get("date_from"), None),
        "end": _parse_date(request.GET.get("date_to"), None),
    }


def _filter_bar(request: HttpRequest, **values: str) -> dict:
    """Options for the filter bar, and its current values echoed from the query string."""
    return {
        "positions": position_options(),
        "workers": [{"id": w.id, "name": w.display_name} for w in _active_employees()],
        "filters": {**{param: request.GET.get(param, "") for param in FILTER_PARAMS}, **values},
    }


@manager_required
@require_GET
def manager_shift_search(request: HttpRequest) -> HttpResponse:
    rows = shift_rows(manager_id=request.user.id, query=request.GET.get("q", "").strip(), **_shift_filters(request))
    sort = request.GET.get("sort") if request.GET.get("sort") in SEARCH_SORTS else "date"
    direction = "desc" if request.GET.get("dir") == "desc" else "asc"
    rows.sort(key=SEARCH_SORTS[sort], reverse=direction == "desc")
    page = Paginator(rows, SEARCH_PAGE_SIZE).get_page(request.GET.get("page"))

    return render_app(
        request,
        page="manager-shift-search",
        title="Search Shifts",
        nav_active="manager_shift_search",
        data={
            **_filter_bar(request, sort=sort, dir=direction),
            "results": page.object_list,
            "total": page.paginator.count,
            "page": page.number,
            "totalPages": page.paginator.num_pages,
            "urls": {"calendar": reverse("manager_shifts")},
        },
    )


def _analytics_rows(request: HttpRequest) -> tuple[dict, list[dict]]:
    """The filters, with the date range defaulting to the 30 days up to today, and the rows they select."""
    filters = _shift_filters(request)
    end = filters["end"] or timezone.localdate()
    start = filters["start"] or end - timedelta(days=ANALYTICS_DEFAULT_DAYS - 1)
    filters["start"], filters["end"] = min(start, end), max(start, end)
    return filters, shift_rows(manager_id=request.user.id, **filters)


@manager_required
@require_GET
def manager_analytics(request: HttpRequest) -> HttpResponse:
    filters, rows = _analytics_rows(request)
    return render_app(
        request,
        page="manager-analytics",
        title="Workforce Analytics",
        nav_active="manager_analytics",
        data={
            **_filter_bar(request, date_from=filters["start"].isoformat(), date_to=filters["end"].isoformat()),
            "analytics": shift_analytics(rows, worker_id=filters["worker_id"]),
            "urls": {"exportCsv": reverse("manager_analytics_export_csv")},
        },
    )


@manager_required
@require_GET
def manager_analytics_export_csv(request: HttpRequest) -> HttpResponse:
    """The shifts behind the dashboard, one per row."""
    filters, rows = _analytics_rows(request)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="shifts-{filters["start"]}-to-{filters["end"]}.csv"'

    writer = csv.writer(response)
    writer.writerow(["Date", "Start", "End", "Position", "Status", "Capacity", "Assigned", "Worker hours", "Workers"])
    for row in rows:
        writer.writerow(
            [
                row["date"],
                row["start_time"],
                row["end_time"],
                row["position"],
                row["status"],
                row["capacity"],
                len(row["workers"]),
                round(row["hours"] * len(row["workers"]), 2),
                "; ".join(worker["name"] for worker in row["workers"]),
            ]
        )
    return response


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
        nav_active="employee_shifts",
        data={
            "anchor": anchor.isoformat(),
            "today": today.isoformat(),
            "shifts": [
                {"id": s.id, **shift_fields(s), "is_past": s.is_past}
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
            "employeeName": request.user.display_name,
            "date": day.isoformat(),
            "unavailable": unavailable,
        }
    )
    notify(
        managers(),
        "Availability updated",
        f"{request.user.display_name} is {'unavailable' if unavailable else 'available again'} on {day:%a %b %d}.",
        actor=request.user,
    )
    return JsonResponse({"ok": True, "date": day.isoformat(), "unavailable": unavailable})
