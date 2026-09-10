from __future__ import annotations

import asyncio
from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User, UserRole
from apps.scheduling.models import EmployeeUnavailability, Position

from .consumers import ScheduleConsumer
from .events import MANAGERS_GROUP

IN_MEMORY_LAYER = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
PING = {"type": "schedule.event", "event": {"type": "ping"}}


def _as_user(user):
    """Stand in for AuthMiddlewareStack: hand the consumer an already-resolved user."""
    consumer = ScheduleConsumer.as_asgi()

    async def app(scope, receive, send):
        return await consumer({**scope, "user": user}, receive, send)

    return app


@override_settings(CHANNEL_LAYERS=IN_MEMORY_LAYER)
class ScheduleConsumerTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.manager = User.objects.create_user(
            username="manager@example.com", password="x", role=UserRole.MANAGER
        )
        cls.employee = User.objects.create_user(
            username="alice@example.com", password="x", role=UserRole.EMPLOYEE
        )

    async def _connect(self, user):
        communicator = WebsocketCommunicator(_as_user(user), "/ws/schedule/")
        connected, _ = await communicator.connect()
        return communicator, connected

    async def test_anonymous_socket_is_rejected(self):
        _, connected = await self._connect(AnonymousUser())
        self.assertFalse(connected)

    async def test_manager_receives_schedule_events(self):
        communicator, connected = await self._connect(self.manager)
        self.assertTrue(connected)

        await get_channel_layer().group_send(MANAGERS_GROUP, PING)
        self.assertEqual(await communicator.receive_json_from(), {"type": "ping"})
        await communicator.disconnect()

    async def test_employee_socket_gets_no_manager_events(self):
        communicator, connected = await self._connect(self.employee)
        self.assertTrue(connected)

        await get_channel_layer().group_send(MANAGERS_GROUP, PING)
        self.assertTrue(await communicator.receive_nothing())
        await communicator.disconnect()


@override_settings(CHANNEL_LAYERS=IN_MEMORY_LAYER)
class LiveAvailabilityTests(TestCase):
    """An employee's availability change reaches managers, both on page load and live."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.barista = Position.objects.create(name="Barista")
        cls.manager = User.objects.create_user(
            username="manager@example.com", password="x", role=UserRole.MANAGER
        )
        cls.alice = User.objects.create_user(
            username="alice@example.com",
            password="x",
            role=UserRole.EMPLOYEE,
            position=cls.barista,
            first_name="Alice",
            last_name="Novak",
        )

    def setUp(self) -> None:
        self.layer = get_channel_layer()
        self.channel = async_to_sync(self.layer.new_channel)()
        async_to_sync(self.layer.group_add)(MANAGERS_GROUP, self.channel)
        self.day = timezone.localdate() + timedelta(days=3)

    def _toggle(self, day):
        self.client.force_login(self.alice)
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            response = self.client.post(
                reverse("employee_unavailability_toggle"), {"date": day.isoformat()}
            )
        return response, callbacks

    def _next_event(self) -> dict:
        async def receive():
            return await asyncio.wait_for(self.layer.receive(self.channel), timeout=1)

        return async_to_sync(receive)()["event"]

    def test_marking_a_day_reaches_managers(self):
        response, _ = self._toggle(self.day)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self._next_event(),
            {
                "type": "unavailability.changed",
                "employeeId": self.alice.id,
                "employeeName": "Alice Novak",
                "date": self.day.isoformat(),
                "unavailable": True,
            },
        )

    def test_clearing_a_day_reaches_managers(self):
        EmployeeUnavailability.objects.create(employee=self.alice, date=self.day)

        self._toggle(self.day)

        self.assertFalse(self._next_event()["unavailable"])

    def test_rejected_toggle_broadcasts_nothing(self):
        response, callbacks = self._toggle(timezone.localdate())

        self.assertEqual(response.status_code, 400)
        self.assertEqual(callbacks, [])

    def test_manager_page_lists_unavailable_days_per_employee(self):
        EmployeeUnavailability.objects.create(employee=self.alice, date=self.day)
        self.client.force_login(self.manager)

        response = self.client.get(reverse("manager_shifts"), {"date": self.day.isoformat()})

        data = response.context["bootstrap"]["data"]
        self.assertEqual(data["unavailability"], {str(self.alice.id): [self.day.isoformat()]})
