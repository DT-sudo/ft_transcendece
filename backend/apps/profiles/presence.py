"""Online status: a user is online while at least one of their pages holds a live socket.

Every socket (`ScheduleConsumer`) counts itself in `User.open_sockets` and refreshes
`User.last_seen` every HEARTBEAT_SECONDS. A count alone would stay stuck if the server
stopped without closing its sockets, so being online also takes a recent `last_seen`;
the next socket after such a stop starts the count over.
"""

from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.realtime.events import send_to_user

from .services import friend_ids

HEARTBEAT_SECONDS = 30
ONLINE_WINDOW = timedelta(seconds=90)


def is_online(user: User) -> bool:
    return user.open_sockets > 0 and user.last_seen is not None and timezone.now() - user.last_seen < ONLINE_WINDOW


def status(user: User) -> dict:
    """`{"online", "lastSeen"}` as the pages and the `friend.status` event carry it."""
    return {"online": is_online(user), "lastSeen": user.last_seen.isoformat() if user.last_seen else None}


def _tell_friends(user: User) -> None:
    event = {"type": "friend.status", "userId": user.pk, "status": status(user)}
    for friend_id in friend_ids(user.pk):
        send_to_user(friend_id, event)


def socket_opened(user_id: int) -> bool:
    """Count a new socket. When it brought the user online, tell their friends and return True."""
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=user_id)
        came_online = not is_online(user)
        user.open_sockets = 1 if came_online else user.open_sockets + 1
        user.last_seen = timezone.now()
        user.save(update_fields=["open_sockets", "last_seen"])
    if came_online:
        _tell_friends(user)
    return came_online


def socket_alive(user_id: int) -> None:
    User.objects.filter(pk=user_id).update(last_seen=timezone.now())


def socket_closed(user_id: int) -> bool:
    """Uncount a socket. When it was the user's last one, tell their friends and return True."""
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=user_id)
        user.open_sockets = max(user.open_sockets - 1, 0)
        user.last_seen = timezone.now()
        user.save(update_fields=["open_sockets", "last_seen"])
    went_offline = user.open_sockets == 0
    if went_offline:
        _tell_friends(user)
    return went_offline
