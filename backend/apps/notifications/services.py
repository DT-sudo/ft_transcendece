"""Store notifications per recipient and push them to the pages the recipient has open."""

from __future__ import annotations

from collections.abc import Iterable

from apps.accounts.models import MANAGER_ROLES, User
from apps.realtime.events import push_to_user

from .models import Notification

HISTORY_LIMIT = 50


def notify(
    recipients: Iterable[User | int], title: str, description: str = "", *, actor: User | None = None, level: str = "info"
) -> None:
    """Notify each recipient except the actor, whose own flash toast already covers the action."""
    actor_id = actor.pk if actor else None
    recipient_ids = {getattr(recipient, "pk", recipient) for recipient in recipients} - {actor_id}
    created = Notification.objects.bulk_create(
        Notification(recipient_id=rid, actor_id=actor_id, level=level, title=title, description=description)
        for rid in sorted(recipient_ids)
    )
    for notification in created:
        push_to_user(notification.recipient_id, {"type": "notification", "notification": notification.as_dict()})


def managers():
    """Every active manager and admin. Employees and positions are one shared directory, so all of them are concerned."""
    return User.objects.filter(role__in=MANAGER_ROLES, is_active=True).values_list("pk", flat=True)


def recent_notifications(user: User, limit: int | None = HISTORY_LIMIT) -> list[dict]:
    """The user's notifications, newest first; `limit=None` returns all of them."""
    return [notification.as_dict() for notification in user.notifications.all()[:limit]]
