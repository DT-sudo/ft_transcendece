from __future__ import annotations

import secrets

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.urls import path

from .events import MANAGERS_GROUP, user_group


class ScheduleConsumer(AsyncJsonWebsocketConsumer):
    """One socket per open page: the user's own notifications, plus schedule changes and presence for managers."""

    # Filled in once connect() accepts; disconnect() also runs for sockets it refused.
    subscriptions = ()
    present = False

    async def connect(self) -> None:
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return
        self.subscriptions = [user_group(user.id)] + ([MANAGERS_GROUP] if user.is_manager else [])
        for group in self.subscriptions:
            await self.channel_layer.group_add(group, self.channel_name)
        # Names this page in presence events; set apart from the user so two tabs show as two.
        self.presence_id = secrets.token_hex(4)
        await self.accept()

    async def disconnect(self, code: int) -> None:
        if self.present:
            await self._to_other_managers({"type": "presence.leave", "id": self.presence_id})
        for group in self.subscriptions:
            await self.channel_layer.group_discard(group, self.channel_name)

    async def receive_json(self, content, **kwargs) -> None:
        """A manager's calendar announces the month it shows and the shift it is editing.

        `hello` marks a page that just (re)connected: the others answer with their own
        presence so it learns who is already there.
        """
        user = self.scope["user"]
        if not user.is_manager or content.get("type") != "presence":
            return
        editing = content.get("editing")
        self.present = True
        await self._to_other_managers(
            {
                "type": "presence",
                "id": self.presence_id,
                "name": user.display_name,
                "month": str(content.get("month", ""))[:7],
                "editing": editing if isinstance(editing, int) else None,
                "hello": bool(content.get("hello")),
            }
        )

    async def _to_other_managers(self, event: dict) -> None:
        await self.channel_layer.group_send(
            MANAGERS_GROUP, {"type": "schedule.event", "event": event, "sender": self.channel_name}
        )

    async def schedule_event(self, message: dict) -> None:
        # A page's own presence is not echoed back to it.
        if message.get("sender") != self.channel_name:
            await self.send_json(message["event"])


websocket_urlpatterns = [path("ws/schedule/", ScheduleConsumer.as_asgi())]
