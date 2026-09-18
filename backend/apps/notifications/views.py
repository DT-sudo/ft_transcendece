"""The signed-in user's notification history behind the header bell."""

from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .models import Notification
from .services import recent_notifications

# An error toast is a sentence or two; anything longer is not one.
MAX_ERROR_TITLE = 100
MAX_ERROR_TEXT = 500


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


@login_required
@require_POST
def record_error(request: HttpRequest) -> JsonResponse:
    """Keep an error the page just showed as a toast in the caller's own history.

    Toasts disappear after a few seconds; the bell is where they can be read again. The
    page sends the text it showed, so this only ever writes to the caller's own list.
    """
    title = (request.POST.get("title") or "").strip()[:MAX_ERROR_TITLE]
    text = (request.POST.get("text") or "").strip()[:MAX_ERROR_TEXT]
    if not text:
        return JsonResponse({"error": "text is required"}, status=400)
    notification = Notification.objects.create(
        recipient=request.user,
        level="error",
        kind="error",
        params={"title": title, "text": text},
        title=title or "Error",
        description=text,
    )
    return JsonResponse({"notification": notification.as_dict()})
