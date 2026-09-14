"""The signed-in user's notification history behind the header bell."""

from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .services import recent_notifications


@login_required
@require_GET
def notification_list(request: HttpRequest) -> JsonResponse:
    """The history as JSON; the bell re-fetches it when a dropped socket reconnects."""
    return JsonResponse({"notifications": recent_notifications(request.user)})


@login_required
@require_POST
def mark_all_read(request: HttpRequest) -> JsonResponse:
    request.user.notifications.filter(read_at__isnull=True).update(read_at=timezone.now())
    return JsonResponse({"ok": True})


@login_required
@require_POST
def clear_all(request: HttpRequest) -> JsonResponse:
    request.user.notifications.all().delete()
    return JsonResponse({"ok": True})
