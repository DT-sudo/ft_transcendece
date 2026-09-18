from __future__ import annotations

import asyncio
from datetime import time, timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Position, User, UserRole
from apps.scheduling.models import EmployeeUnavailability, Shift

from .consumers import ScheduleConsumer
from .events import EVERYONE_GROUP, MANAGERS_GROUP, user_group

IN_MEMORY_LAYER = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
PING = {"type": "schedule.event", "event": {"type": "ping"}}


def next_event(layer, channel) -> dict:
    """The next event broadcast to `channel`, failing after a second instead of hanging."""

    async def receive():
        return await asyncio.wait_for(layer.receive(channel), timeout=1)

    return async_to_sync(receive)()["event"]


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
        cls.other_manager = User.objects.create_user(
            username="tom@example.com", password="x", role=UserRole.MANAGER, first_name="Tom"
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

    async def test_employee_receives_only_their_own_events(self):
        communicator, connected = await self._connect(self.employee)
        self.assertTrue(connected)

        await get_channel_layer().group_send(MANAGERS_GROUP, PING)
        await get_channel_layer().group_send(
            user_group(self.employee.id), {"type": "schedule.event", "event": {"type": "mine"}}
        )
        # The managers' ping never arrives, so their own event is the first message.
        self.assertEqual(await communicator.receive_json_from(), {"type": "mine"})
        await communicator.disconnect()

    async def test_presence_reaches_the_other_managers_but_not_the_sender(self):
        mine, _ = await self._connect(self.manager)
        theirs, _ = await self._connect(self.other_manager)

        await mine.send_json_to({"type": "presence", "month": "2026-09", "editing": 7, "hello": True})

        event = await theirs.receive_json_from()
        self.assertEqual(
            {key: event[key] for key in ("type", "name", "month", "editing", "hello")},
            {"type": "presence", "name": "manager@example.com", "month": "2026-09", "editing": 7, "hello": True},
        )
        self.assertTrue(await mine.receive_nothing())

        # Closing the page tells the others it left.
        await mine.disconnect()
        self.assertEqual(await theirs.receive_json_from(), {"type": "presence.leave", "id": event["id"]})
        await theirs.disconnect()

    async def test_employee_presence_is_ignored(self):
        employee, _ = await self._connect(self.employee)
        manager, _ = await self._connect(self.manager)

        await employee.send_json_to({"type": "presence", "month": "2026-09"})

        self.assertTrue(await manager.receive_nothing())
        await employee.disconnect()
        await manager.disconnect()


@override_settings(CHANNEL_LAYERS=IN_MEMORY_LAYER)
class LiveAvailabilityTests(TestCase):
    """Availability and shift changes reach managers, both on page load and live."""

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
        return next_event(self.layer, self.channel)

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

    def test_shift_write_reaches_managers(self):
        shift = Shift.objects.create(
            date=self.day, start_time=time(9, 0), end_time=time(17, 0), position=self.barista, created_by=self.manager
        )
        self.client.force_login(self.manager)

        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(reverse("delete_shift", args=[shift.id]))

        self.assertEqual(self._next_event(), {"type": "shifts.changed"})

    def test_calendar_refetches_its_data_as_json(self):
        Shift.objects.create(
            date=self.day, start_time=time(9, 0), end_time=time(17, 0), position=self.barista, created_by=self.manager
        )
        self.client.force_login(self.manager)

        data = self.client.get(reverse("manager_shifts"), {"date": self.day.isoformat(), "format": "json"}).json()

        self.assertEqual([(shift["start_time"], shift["version"]) for shift in data["shifts"]], [("09:00", 1)])

    def test_manager_page_lists_unavailable_days_per_employee(self):
        EmployeeUnavailability.objects.create(employee=self.alice, date=self.day)
        self.client.force_login(self.manager)

        response = self.client.get(reverse("manager_shifts"), {"date": self.day.isoformat()})

        data = response.context["bootstrap"]["data"]
        self.assertEqual(data["unavailability"], {str(self.alice.id): [self.day.isoformat()]})


@override_settings(CHANNEL_LAYERS=IN_MEMORY_LAYER)
class LiveDirectoryTests(TestCase):
    """Account, role and position writes reach every open page, whatever role it belongs to."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.barista = Position.objects.create(name="Barista")
        cls.admin = User.objects.create_user(username="admin@example.com", email="admin@example.com", role=UserRole.ADMIN)
        cls.employee = User.objects.create_user(
            username="alice@example.com", email="alice@example.com", password="x",
            role=UserRole.EMPLOYEE, position=cls.barista,
        )

    def setUp(self) -> None:
        self.layer = get_channel_layer()
        self.channel = async_to_sync(self.layer.new_channel)()
        # The group an employee's page is in too, not only a manager's.
        async_to_sync(self.layer.group_add)(EVERYONE_GROUP, self.channel)
        self.client.force_login(self.admin)

    def _post(self, url_name, *args, **data):
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(reverse(url_name, args=args), data)

    def _events(self) -> list[dict]:
        """Everything broadcast to the group, until it goes quiet."""
        events = []
        while True:
            try:
                events.append(next_event(self.layer, self.channel))
            except TimeoutError:
                return events

    def test_creating_an_account_reaches_every_page(self):
        self._post("manager_employees_create", full_name="New Hire", email="new@example.com",
                   role=UserRole.EMPLOYEE, position=self.barista.id)

        self.assertIn({"type": "directory.changed"}, self._events())

    def test_deleting_an_account_reaches_every_page(self):
        self._post("employee_delete", self.employee.id)

        self.assertIn({"type": "directory.changed"}, self._events())

    def test_adding_and_removing_a_position_reaches_every_page(self):
        self._post("position_create", name="Cook")
        self.assertIn({"type": "directory.changed"}, self._events())

        self._post("position_delete", Position.objects.get(name="Cook").id)
        self.assertIn({"type": "directory.changed"}, self._events())

    def test_a_role_change_tells_that_accounts_pages_to_sign_out(self):
        theirs = async_to_sync(self.layer.new_channel)()
        async_to_sync(self.layer.group_add)(user_group(self.employee.id), theirs)

        self._post("employee_update", self.employee.id, full_name="Alice N",
                   email=self.employee.email, role=UserRole.MANAGER, position="")

        events = []
        while True:
            try:
                events.append(next_event(self.layer, theirs))
            except TimeoutError:
                break
        self.assertIn({"type": "session.ended"}, events)
