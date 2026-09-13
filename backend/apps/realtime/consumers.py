from __future__ import annotations

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.urls import path

from .events import MANAGERS_GROUP


class ScheduleConsumer(AsyncJsonWebsocketConsumer):
    """One socket per open manager page, subscribed to the group that receives schedule changes."""

    async def connect(self) -> None:
        user = self.scope["user"]
        if not (user.is_authenticated and user.is_manager):
            await self.close()
            return
        await self.channel_layer.group_add(MANAGERS_GROUP, self.channel_name)
        await self.accept()

    async def disconnect(self, code: int) -> None:
        await self.channel_layer.group_discard(MANAGERS_GROUP, self.channel_name)

    async def schedule_event(self, message: dict) -> None:
        await self.send_json(message["event"])


websocket_urlpatterns = [path("ws/schedule/", ScheduleConsumer.as_asgi())]
