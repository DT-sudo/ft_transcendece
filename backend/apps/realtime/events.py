"""Push schedule changes to the pages that are open right now."""

from __future__ import annotations

import logging
from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction

logger = logging.getLogger(__name__)

# Employees and positions are one shared directory today, so every manager sees
# every employee's availability. Becomes a per-organization group later.
MANAGERS_GROUP = "managers"


def _send(group: str, event: dict[str, Any]) -> None:
    try:
        async_to_sync(get_channel_layer().group_send)(group, {"type": "schedule.event", "event": event})
    except Exception:
        # The write has already committed; a broadcast failure must not turn it into an error.
        logger.exception("Could not broadcast %s", event.get("type"))


def user_group(user_id: int) -> str:
    """The pages one user has open, for events addressed to them alone."""
    return f"user_{user_id}"


def notify_managers(event: dict[str, Any]) -> None:
    """Send `event` to every connected manager once the current transaction commits."""
    transaction.on_commit(lambda: _send(MANAGERS_GROUP, event))


def send_to_user(user_id: int, event: dict[str, Any]) -> None:
    """Send `event` to every page `user_id` has open, right away."""
    _send(user_group(user_id), event)


def push_to_user(user_id: int, event: dict[str, Any]) -> None:
    """Send `event` to every page `user_id` has open once the current transaction commits."""
    transaction.on_commit(lambda: send_to_user(user_id, event))
