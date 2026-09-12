from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET

from apps.accounts.decorators import manager_required
from apps.frontend.shell import render_app

from ..services import search_manager_shifts
from .helpers import _parse_int, _parse_int_list, _parse_optional_date, _shift_filter_options

VALID_SORTS = {"date", "start_time", "worker", "position"}
PAGE_SIZE_CHOICES = (10, 25, 50, 100)


def _build_result_payload(rows: list[dict]) -> list[dict]:
    now_local = timezone.localtime()
    today = now_local.date()
    current_time = now_local.time().replace(tzinfo=None)

    payload = []
    for row in rows:
        shift = row["shift"]
        is_past = shift.date < today or (shift.date == today and shift.end_time < current_time)
        payload.append(
            {
                "id": shift.id,
                "date": shift.date.isoformat(),
                "start_time": shift.start_time.strftime("%H:%M"),
                "end_time": shift.end_time.strftime("%H:%M"),
                "position": shift.position.name,
                "position_id": shift.position_id,
                "capacity": shift.capacity,
                "assigned_count": len(row["worker_ids"]),
                "assigned_employee_ids": row["worker_ids"],
                "worker_names": row["worker_names"],
                "manager_name": row["manager_name"],
                "duration_hours": row["duration_hours"],
                "status": shift.status,
                "is_past": is_past,
            }
        )
    return payload


@manager_required
@require_GET
def manager_shift_search(request: HttpRequest) -> HttpResponse:
    query = (request.GET.get("q") or "").strip()
    position_ids = _parse_int_list(request, "position")
    worker_ids = _parse_int_list(request, "worker")
    manager_ids = _parse_int_list(request, "manager")
    status = (request.GET.get("status") or "").lower()
    date_from = _parse_optional_date(request.GET.get("date_from"))
    date_to = _parse_optional_date(request.GET.get("date_to"))

    sort = (request.GET.get("sort") or "date").lower()
    if sort not in VALID_SORTS:
        sort = "date"
    direction = (request.GET.get("dir") or "asc").lower()
    if direction not in {"asc", "desc"}:
        direction = "asc"

    page = _parse_int(request.GET.get("page"), 1)
    page_size = _parse_int(request.GET.get("page_size"), 25)
    if page_size not in PAGE_SIZE_CHOICES:
        page_size = 25

    result = search_manager_shifts(
        manager_id=request.user.id,
        query=query,
        position_ids=position_ids or None,
        worker_ids=worker_ids or None,
        manager_ids=manager_ids or None,
        status=status or None,
        start=date_from,
        end=date_to,
        sort=sort,
        direction=direction,
        page=page,
        page_size=page_size,
    )

    return render_app(
        request,
        entry="manager-shift-search",
        title="Search Shifts",
        description="PlanShift - Advanced shift search",
        body_class="manager-search-page",
        nav_active="manager_shifts",
        data={
            **_shift_filter_options(request),
            "results": _build_result_payload(result["rows"]),
            "total": result["total"],
            "page": result["page"],
            "pageSize": result["page_size"],
            "totalPages": result["total_pages"],
            "pageSizeChoices": list(PAGE_SIZE_CHOICES),
            "filters": {
                "q": query,
                "position": [str(v) for v in position_ids],
                "worker": [str(v) for v in worker_ids],
                "manager": [str(v) for v in manager_ids],
                "status": status,
                "dateFrom": date_from.isoformat() if date_from else "",
                "dateTo": date_to.isoformat() if date_to else "",
                "sort": sort,
                "dir": direction,
            },
            "urls": {
                "search": reverse("manager_shift_search"),
                "calendar": reverse("manager_shifts"),
            },
        },
    )
