from __future__ import annotations

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.urls import path

from .events import MANAGERS_GROUP, user_group


class ScheduleConsumer(AsyncJsonWebsocketConsumer):
    """One socket per open page: the user's own notifications, plus schedule changes for managers."""

    # Filled in once connect() accepts; disconnect() also runs for sockets it refused.
    subscriptions = ()

    async def connect(self) -> None:
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return
        self.subscriptions = [user_group(user.id)] + ([MANAGERS_GROUP] if user.is_manager else [])
        for group in self.subscriptions:
            await self.channel_layer.group_add(group, self.channel_name)
        await self.accept()

    async def disconnect(self, code: int) -> None:
        for group in self.subscriptions:
            await self.channel_layer.group_discard(group, self.channel_name)

    async def schedule_event(self, message: dict) -> None:
        await self.send_json(message["event"])


websocket_urlpatterns = [path("ws/schedule/", ScheduleConsumer.as_asgi())]
