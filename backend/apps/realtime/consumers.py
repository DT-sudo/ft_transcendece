from __future__ import annotations

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.urls import path

from .events import MANAGERS_GROUP


class ScheduleConsumer(AsyncJsonWebsocketConsumer):
    """One socket per open page; managers join the group that receives schedule changes."""

    async def connect(self) -> None:
        user = self.scope.get("user")
        if user is None or not user.is_authenticated:
            await self.close()
            return

        self.joined_groups = [MANAGERS_GROUP] if user.is_manager else []
        for group in self.joined_groups:
            await self.channel_layer.group_add(group, self.channel_name)
        await self.accept()

    async def disconnect(self, code: int) -> None:
        for group in getattr(self, "joined_groups", []):
            await self.channel_layer.group_discard(group, self.channel_name)

    async def schedule_event(self, message: dict) -> None:
        await self.send_json(message["event"])


websocket_urlpatterns = [path("ws/schedule/", ScheduleConsumer.as_asgi())]
