from __future__ import annotations

from datetime import time, timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User, UserRole
from apps.realtime.events import user_group
from apps.realtime.tests import IN_MEMORY_LAYER, next_event
from apps.scheduling.models import Assignment, Position, Shift, ShiftStatus

from .models import Notification


class NotificationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.barista = Position.objects.create(name="Barista")
        cls.manager = User.objects.create_user(
            username="manager@example.com", password="x", role=UserRole.MANAGER, first_name="Maya", last_name="Lee"
        )
        cls.other_manager = User.objects.create_user(
            username="other@example.com", password="x", role=UserRole.MANAGER
        )
        cls.alice, cls.bob, cls.carol = (
            User.objects.create_user(
                username=f"{name}@example.com",
                email=f"{name}@example.com",
                password="x",
                role=UserRole.EMPLOYEE,
                position=cls.barista,
                first_name=name.title(),
            )
            for name in ("alice", "bob", "carol")
        )
        cls.day = timezone.localdate() + timedelta(days=3)

    def _shift(self, *, status=ShiftStatus.PUBLISHED, employees=(), start=time(9, 0), end=time(17, 0)) -> Shift:
        shift = Shift.objects.create(
            date=self.day, start_time=start, end_time=end, capacity=2, position=self.barista,
            created_by=self.manager, status=status,
        )
        Assignment.objects.bulk_create(Assignment(shift=shift, employee=employee) for employee in employees)
        return shift

    def _post(self, user, name, *args, data=None):
        self.client.force_login(user)
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(reverse(name, args=args), data or {})

    def _received(self) -> dict[User, list[str]]:
        """Every notification created so far, as {recipient: [titles]}."""
        received: dict[User, list[str]] = {}
        for notification in Notification.objects.select_related("recipient").order_by("id"):
            received.setdefault(notification.recipient, []).append(notification.title)
        return received


@override_settings(CHANNEL_LAYERS=IN_MEMORY_LAYER)
class RecipientTests(NotificationTestCase):
    """Each write notifies the people it concerns, and never the person who made it."""

    def _shift_form(self, shift: Shift, employees, *, start="09:00", end="17:00") -> dict:
        return {
            "date": shift.date.isoformat(),
            "start_time": start,
            "end_time": end,
            "position": self.barista.id,
            "capacity": 2,
            "employee_ids": [employee.id for employee in employees],
            "version": shift.version,
        }

    def test_publishing_a_shift_notifies_its_employees(self):
        shift = self._shift(status=ShiftStatus.DRAFT, employees=[self.alice])

        self._post(self.manager, "publish_shift", shift.id)

        self.assertEqual(self._received(), {self.alice: ["New shift published"]})

    def test_publish_all_sends_one_notification_per_employee(self):
        self._shift(status=ShiftStatus.DRAFT, employees=[self.alice, self.bob])
        self._shift(status=ShiftStatus.DRAFT, employees=[self.alice], start=time(18, 0), end=time(20, 0))

        self._post(self.manager, "publish_all_shifts", data={"date": self.day.isoformat()})

        self.assertEqual(
            self._received(), {self.alice: ["2 new shifts published"], self.bob: ["New shift published"]}
        )

    def test_editing_a_draft_notifies_nobody(self):
        shift = self._shift(status=ShiftStatus.DRAFT, employees=[self.alice])

        self._post(self.manager, "update_shift", shift.id, data=self._shift_form(shift, [self.bob], start="10:00"))

        self.assertEqual(self._received(), {})

    def test_editing_a_published_shift_tells_each_employee_what_changed_for_them(self):
        shift = self._shift(employees=[self.alice, self.bob])

        self._post(
            self.manager, "update_shift", shift.id, data=self._shift_form(shift, [self.alice, self.carol], start="10:00")
        )

        self.assertEqual(
            self._received(),
            {self.alice: ["Shift changed"], self.bob: ["Removed from a shift"], self.carol: ["New shift assigned"]},
        )

    def test_deleting_a_published_shift_notifies_its_employees(self):
        shift = self._shift(employees=[self.alice])

        self._post(self.manager, "delete_shift", shift.id)

        self.assertEqual(self._received(), {self.alice: ["Shift cancelled"]})

    def test_position_changes_notify_the_other_managers(self):
        self._post(self.manager, "position_create", data={"name": "Cook"})
        self._post(self.manager, "position_delete", Position.objects.get(name="Cook").id)

        self.assertEqual(self._received(), {self.other_manager: ["Position created", "Position deleted"]})

    def test_employee_changes_notify_the_other_managers_and_the_employee(self):
        self._post(
            self.manager,
            "employee_update",
            self.alice.id,
            data={"full_name": "Alice Novak", "email": "alice@example.com", "position": self.barista.id},
        )
        self._post(self.manager, "reset_employee_password", self.alice.id)

        self.assertEqual(
            self._received(),
            {
                self.other_manager: ["Employee updated"],
                self.alice: ["Your details were updated", "Your password was reset"],
            },
        )

    def test_deleting_an_employee_notifies_the_other_managers(self):
        self._post(self.manager, "employee_delete", self.bob.id)

        self.assertEqual(self._received(), {self.other_manager: ["Employee deleted"]})

    def test_unavailability_notifies_every_manager(self):
        self._post(self.alice, "employee_unavailability_toggle", data={"date": self.day.isoformat()})

        self.assertEqual(
            self._received(), {self.manager: ["Availability updated"], self.other_manager: ["Availability updated"]}
        )

    def test_notification_is_pushed_to_the_recipients_open_pages(self):
        layer = get_channel_layer()
        channel = async_to_sync(layer.new_channel)()
        async_to_sync(layer.group_add)(user_group(self.alice.id), channel)
        shift = self._shift(employees=[self.alice])

        self._post(self.manager, "delete_shift", shift.id)

        # Their open calendar is told to refresh first, then the notification follows.
        self.assertEqual(next_event(layer, channel), {"type": "shifts.changed"})
        event = next_event(layer, channel)
        self.assertEqual(event["type"], "notification")
        self.assertEqual(event["notification"]["title"], "Shift cancelled")
        self.assertFalse(event["notification"]["read"])


class HistoryTests(NotificationTestCase):
    """The bell's history is per recipient and lives on the server."""

    def setUp(self) -> None:
        Notification.objects.create(recipient=self.alice, title="For Alice")
        Notification.objects.create(recipient=self.bob, title="For Bob")

    def test_page_payload_carries_only_the_users_own_notifications(self):
        self.client.force_login(self.alice)

        response = self.client.get(reverse("employee_shifts"))

        items = response.context["bootstrap"]["notifications"]["items"]
        self.assertEqual([item["title"] for item in items], ["For Alice"])

    def test_mark_all_read_touches_only_the_callers_notifications(self):
        self._post(self.alice, "notifications_mark_read")

        self.assertIsNotNone(Notification.objects.get(recipient=self.alice).read_at)
        self.assertIsNone(Notification.objects.get(recipient=self.bob).read_at)

    def test_clear_deletes_only_the_callers_notifications(self):
        self._post(self.alice, "notifications_clear")

        self.assertEqual(list(Notification.objects.values_list("title", flat=True)), ["For Bob"])

    def test_list_endpoint_returns_the_history(self):
        self.client.force_login(self.alice)

        payload = self.client.get(reverse("notifications")).json()

        self.assertEqual([item["title"] for item in payload["notifications"]], ["For Alice"])
