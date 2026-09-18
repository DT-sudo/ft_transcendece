from __future__ import annotations

from datetime import time, timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Position, User, UserRole
from apps.realtime.events import user_group
from apps.realtime.tests import IN_MEMORY_LAYER, next_event
from apps.scheduling.models import Assignment, Shift, ShiftStatus

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
        # Accounts and positions are the admin's to write.
        cls.admin = User.objects.create_user(
            username="admin@example.com", password="x", role=UserRole.ADMIN, first_name="Ada", last_name="Ray"
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

        self.assertEqual(self._received(), {self.alice: ["New shift assigned"]})

    def test_publish_all_sends_one_notification_per_employee(self):
        self._shift(status=ShiftStatus.DRAFT, employees=[self.alice, self.bob])
        self._shift(status=ShiftStatus.DRAFT, employees=[self.alice], start=time(18, 0), end=time(20, 0))

        self._post(self.manager, "publish_all_shifts", data={"date": self.day.isoformat()})

        self.assertEqual(
            self._received(), {self.alice: ["2 new shifts assigned"], self.bob: ["New shift assigned"]}
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

    def test_position_changes_notify_the_managers(self):
        self._post(self.admin, "position_create", data={"name": "Cook"})
        self._post(self.admin, "position_delete", Position.objects.get(name="Cook").id)

        self.assertEqual(
            self._received(),
            {
                self.manager: ["Position created", "Position deleted"],
                self.other_manager: ["Position created", "Position deleted"],
            },
        )

    def test_employee_changes_notify_the_managers_and_the_employee(self):
        self._post(
            self.admin,
            "employee_update",
            self.alice.id,
            data={
                "full_name": "Alice Novak",
                "email": "alice@example.com",
                "role": UserRole.EMPLOYEE,
                "position": self.barista.id,
            },
        )
        self._post(self.admin, "reset_employee_password", self.alice.id)

        self.assertEqual(
            self._received(),
            {
                self.manager: ["Employee updated"],
                self.other_manager: ["Employee updated"],
                self.alice: ["Your details were updated", "Your password was reset"],
            },
        )

    def test_deleting_an_employee_notifies_the_managers(self):
        self._post(self.admin, "employee_delete", self.bob.id)

        self.assertEqual(self._received(), {self.manager: ["Employee deleted"], self.other_manager: ["Employee deleted"]})

    def test_deleting_an_employee_with_upcoming_shifts_tells_the_managers_which(self):
        self._shift(employees=[self.bob])
        self._post(self.admin, "employee_delete", self.bob.id)
        came_off = "Bob came off 1 upcoming shift"
        self.assertEqual(
            self._received(),
            {self.manager: [came_off, "Employee deleted"], self.other_manager: [came_off, "Employee deleted"]},
        )

    def test_an_employee_deleting_their_account_tells_the_managers_which_shifts_they_left(self):
        self.bob.set_password("pw")
        self.bob.save()
        self._shift(employees=[self.bob])
        self._post(self.bob, "privacy_delete_account", data={"confirm_email": self.bob.email, "confirm_password": "pw"})
        came_off = ["Bob came off 1 upcoming shift"]
        self.assertEqual(self._received(), {self.manager: came_off, self.other_manager: came_off, self.admin: came_off})

    def _signed_in(self, user) -> Client:
        client = Client()
        client.force_login(user)
        return client

    def _update_alice(self, **fields):
        self._post(
            self.admin,
            "employee_update",
            self.alice.id,
            data={"full_name": "Alice", "email": "alice@example.com", "role": UserRole.EMPLOYEE, **fields},
        )
        return Notification.objects.get(recipient=self.alice)

    def test_a_new_position_names_the_old_and_new_one_and_signs_the_employee_out(self):
        cook = Position.objects.create(name="Cook")
        alices_browser = self._signed_in(self.alice)

        notification = self._update_alice(position=cook.id)

        self.assertEqual(notification.title, "Your position was changed")
        self.assertEqual(notification.description, "Ada Ray changed your position from \u201cBarista\u201d to \u201cCook\u201d.")
        self.assertRedirects(alices_browser.get(reverse("employee_shifts")), reverse("login"), fetch_redirect_response=False)

    def test_a_new_role_names_the_old_and_new_one_and_signs_the_account_out(self):
        alices_browser = self._signed_in(self.alice)

        notification = self._update_alice(role=UserRole.MANAGER, position="")

        self.assertEqual(notification.title, "Your role was changed")
        self.assertEqual(notification.description, "Ada Ray changed your role from Employee to Manager.")
        self.assertRedirects(alices_browser.get(reverse("employee_shifts")), reverse("login"), fetch_redirect_response=False)

    def test_unavailability_notifies_every_manager(self):
        self._post(self.alice, "employee_unavailability_toggle", data={"date": self.day.isoformat()})

        self.assertEqual(
            self._received(),
            {
                self.manager: ["Availability updated"],
                self.other_manager: ["Availability updated"],
                self.admin: ["Availability updated"],
            },
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


class PositionDeletionTests(NotificationTestCase):
    """A deleted position takes its upcoming shifts with it; its worked shifts stay as history."""

    def test_worked_shifts_keep_the_position_name_and_upcoming_ones_are_deleted(self):
        worked = self._shift(employees=[self.alice])
        worked.date = timezone.localdate() - timedelta(days=2)
        worked.save()
        upcoming = self._shift(employees=[self.alice])
        # Started today (the whole day long): already history, kept like a worked one.
        started = self._shift(employees=[self.alice], start=time(0, 0), end=time(23, 59))
        started.date = timezone.localdate()
        started.save()
        self.assertTrue(started.is_past)

        self._post(self.admin, "position_delete", self.barista.id)

        worked.refresh_from_db()
        self.assertEqual((worked.position, worked.position_name), (None, "Barista"))
        self.assertTrue(worked.assignments.filter(employee=self.alice).exists())
        self.assertFalse(Shift.objects.filter(pk=upcoming.pk).exists())
        started.refresh_from_db()
        self.assertEqual(started.position_name, "Barista")
        self.alice.refresh_from_db()
        self.assertIsNone(self.alice.position)
        self.assertEqual(
            self._received()[self.alice], ["Shift cancelled", "Your position was removed"]
        )
        self.assertEqual(
            self._received()[self.manager], ["Position deleted", "1 upcoming shift of Barista deleted"]
        )


class ErrorHistoryTests(NotificationTestCase):
    """Errors shown as toasts are kept in the caller's own history."""

    def test_recorded_error_joins_only_the_callers_history(self):
        self.client.force_login(self.manager)
        payload = self.client.post(
            reverse("notifications_record_error"), {"text": "End time must be after start time."}
        ).json()["notification"]

        self.assertEqual((payload["level"], payload["title"]), ("error", "Error"))
        self.assertEqual(payload["description"], "End time must be after start time.")
        self.assertEqual(Notification.objects.get().recipient, self.manager)

    def test_an_empty_error_is_refused(self):
        self.client.force_login(self.manager)
        response = self.client.post(reverse("notifications_record_error"), {"text": " "})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Notification.objects.exists())


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
