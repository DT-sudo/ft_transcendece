"""Store notifications per recipient and push them to the pages the recipient has open."""

from __future__ import annotations

from collections.abc import Iterable

from django.conf import settings
from django.utils import translation

from apps.accounts.models import MANAGER_ROLES, User
from apps.realtime.events import push_to_user

from .messages import render
from .models import Notification

HISTORY_LIMIT = 50


def notify(
    recipients: Iterable[User | int], kind: str, *, actor: User | None = None, level: str = "info", **params
) -> None:
    """Notify each recipient except the actor, whose own flash toast already covers the action.

    `kind` names the message in `messages.py` and `params` are the facts it is written from.
    A live push is written in its recipient's language, which may not be the actor's.
    """
    actor_id = actor.pk if actor else None
    recipient_ids = {getattr(recipient, "pk", recipient) for recipient in recipients} - {actor_id}
    if not recipient_ids:
        return
    with translation.override("en"):
        title, description = render(kind, params)
    created = Notification.objects.bulk_create(
        Notification(
            recipient_id=rid,
            actor_id=actor_id,
            level=level,
            kind=kind,
            params=params,
            title=title[:100],
            description=description,
        )
        for rid in sorted(recipient_ids)
    )
    languages = dict(User.objects.filter(pk__in=recipient_ids).values_list("pk", "language"))
    for notification in created:
        with translation.override(languages.get(notification.recipient_id) or settings.LANGUAGE_CODE):
            payload = notification.as_dict()
        push_to_user(notification.recipient_id, {"type": "notification", "notification": payload})


def managers():
    """Every active manager and admin. Employees and positions are one shared directory, so all of them are concerned."""
    return User.objects.filter(role__in=MANAGER_ROLES, is_active=True).values_list("pk", flat=True)


def recent_notifications(user: User, limit: int | None = HISTORY_LIMIT) -> list[dict]:
    """The user's notifications, newest first, in the active language; `limit=None` returns all of them."""
    return [notification.as_dict() for notification in user.notifications.all()[:limit]]
