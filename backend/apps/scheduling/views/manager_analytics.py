from __future__ import annotations

import csv
from datetime import timedelta

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET

from apps.accounts.decorators import manager_required
from apps.frontend.shell import render_app

from ..services import compute_shift_analytics
from .helpers import _parse_int_list, _parse_optional_date, _shift_filter_options

DEFAULT_RANGE_DAYS = 29  # 30 days inclusive of today


def _default_range(today):
    return today - timezone.timedelta(days=DEFAULT_RANGE_DAYS), today


def _read_filters(request: HttpRequest):
    today = timezone.localdate()
    default_start, default_end = _default_range(today)

    start = _parse_optional_date(request.GET.get("date_from")) or default_start
    end = _parse_optional_date(request.GET.get("date_to")) or default_end
    if start > end:
        start, end = end, start

    return {
        "start": start,
        "end": end,
        "position_ids": _parse_int_list(request, "position") or None,
        "worker_ids": _parse_int_list(request, "worker") or None,
        "manager_ids": _parse_int_list(request, "manager") or None,
        "status": (request.GET.get("status") or "").lower() or None,
    }


def _serialize_analytics(analytics: dict) -> dict:
    """Drop the ORM rows from the payload sent to the browser (CSV export
    re-derives them server-side); everything else is already JSON-safe."""
    return {"kpis": analytics["kpis"], "charts": analytics["charts"], "top": analytics["top"]}


@manager_required
@require_GET
def manager_analytics(request: HttpRequest) -> HttpResponse:
    filters = _read_filters(request)
    analytics = compute_shift_analytics(manager_id=request.user.id, **filters)

    return render_app(
        request,
        entry="manager-analytics",
        title="Workforce Analytics",
        description="PlanShift - Workforce analytics dashboard",
        body_class="manager-analytics-page",
        nav_active="manager_shifts",
        data={
            **_shift_filter_options(request),
            "analytics": _serialize_analytics(analytics),
            "filters": {
                "dateFrom": filters["start"].isoformat(),
                "dateTo": filters["end"].isoformat(),
                "position": [str(v) for v in (filters["position_ids"] or [])],
                "worker": [str(v) for v in (filters["worker_ids"] or [])],
                "manager": [str(v) for v in (filters["manager_ids"] or [])],
                "status": filters["status"] or "",
            },
            "today": timezone.localdate().isoformat(),
            "urls": {
                "data": reverse("manager_analytics_data"),
                "exportCsv": reverse("manager_analytics_export_csv"),
                "calendar": reverse("manager_shifts"),
            },
        },
    )


@manager_required
@require_GET
def manager_analytics_data(request: HttpRequest) -> JsonResponse:
    """JSON refresh endpoint: same filters as the page, used for client-side
    updates when filters change and for the dashboard's periodic polling
    (there's no push/websocket layer in this project, so "real-time" here
    means the dashboard quietly re-fetches on an interval)."""
    filters = _read_filters(request)
    analytics = compute_shift_analytics(manager_id=request.user.id, **filters)
    return JsonResponse(
        {
            "ok": True,
            "generatedAt": timezone.now().isoformat(),
            **_serialize_analytics(analytics),
        }
    )


@manager_required
@require_GET
def manager_analytics_export_csv(request: HttpRequest) -> HttpResponse:
    """Raw shift rows for the current filter set, for the Export > CSV action."""
    filters = _read_filters(request)
    analytics = compute_shift_analytics(manager_id=request.user.id, **filters)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="shift-analytics-{filters["start"]}-to-{filters["end"]}.csv"'
    )

    writer = csv.writer(response)
    writer.writerow(
        ["Date", "Start", "End", "Position", "Status", "Capacity", "Assigned", "Hours", "Workers", "Manager"]
    )
    for row in analytics["rows"]:
        shift = row["shift"]
        writer.writerow(
            [
                shift.date.isoformat(),
                shift.start_time.strftime("%H:%M"),
                shift.end_time.strftime("%H:%M"),
                shift.position.name,
                shift.status,
                shift.capacity,
                len(row["worker_ids"]),
                row["duration_hours"] * len(row["worker_ids"]),
                "; ".join(row["worker_names"]),
                row["manager_name"],
            ]
        )
    return response
