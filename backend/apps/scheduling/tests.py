from __future__ import annotations

from datetime import date, time, timedelta

from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Position, User, UserRole

from .models import Assignment, EmployeeUnavailability, Shift
from .services import STALE_SHIFT, assign_employees_to_shift, shifts_for_employee


class HardConstraintTests(TestCase):
    """Covers the four scheduling rules enforced in services.assign_employees_to_shift."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.barista = Position.objects.create(name="Barista")
        cls.chef = Position.objects.create(name="Head Chef")

        cls.manager = User.objects.create_user(
            username="manager@example.com", password="x", role=UserRole.MANAGER
        )
        cls.alice = User.objects.create_user(
            username="alice@example.com", password="x", role=UserRole.EMPLOYEE, position=cls.barista
        )
        cls.bob = User.objects.create_user(
            username="bob@example.com", password="x", role=UserRole.EMPLOYEE, position=cls.barista
        )
        cls.carol = User.objects.create_user(
            username="carol@example.com", password="x", role=UserRole.EMPLOYEE, position=cls.chef
        )
        cls.day = date(2030, 6, 3)

    def _shift(self, *, start=time(9, 0), end=time(17, 0), capacity=2, position=None) -> Shift:
        return Shift.objects.create(
            date=self.day,
            start_time=start,
            end_time=end,
            capacity=capacity,
            position=position or self.barista,
            created_by=self.manager,
        )

    def test_valid_assignment_is_persisted(self):
        shift = self._shift()
        assign_employees_to_shift(shift, [self.alice.id, self.bob.id])
        self.assertEqual(Assignment.objects.filter(shift=shift).count(), 2)

    def test_position_mismatch_is_rejected(self):
        shift = self._shift()
        with self.assertRaises(ValidationError):
            assign_employees_to_shift(shift, [self.carol.id])
        self.assertFalse(Assignment.objects.filter(shift=shift).exists())

    def test_capacity_overflow_is_rejected(self):
        shift = self._shift(capacity=1)
        with self.assertRaises(ValidationError):
            assign_employees_to_shift(shift, [self.alice.id, self.bob.id])
        self.assertFalse(Assignment.objects.filter(shift=shift).exists())

    def test_unavailable_employee_is_rejected(self):
        EmployeeUnavailability.objects.create(employee=self.alice, date=self.day)
        shift = self._shift()
        with self.assertRaises(ValidationError):
            assign_employees_to_shift(shift, [self.alice.id])

    def test_overlapping_shifts_are_rejected(self):
        morning = self._shift(start=time(9, 0), end=time(13, 0))
        assign_employees_to_shift(morning, [self.alice.id])

        overlapping = self._shift(start=time(12, 0), end=time(18, 0))
        with self.assertRaises(ValidationError):
            assign_employees_to_shift(overlapping, [self.alice.id])

    def test_back_to_back_shifts_are_allowed(self):
        morning = self._shift(start=time(9, 0), end=time(13, 0))
        assign_employees_to_shift(morning, [self.alice.id])

        afternoon = self._shift(start=time(13, 0), end=time(18, 0))
        assign_employees_to_shift(afternoon, [self.alice.id])
        self.assertEqual(Assignment.objects.filter(employee=self.alice).count(), 2)

    def test_duplicate_ids_are_deduplicated_before_capacity_check(self):
        shift = self._shift(capacity=1)
        assign_employees_to_shift(shift, [self.alice.id, self.alice.id])
        self.assertEqual(Assignment.objects.filter(shift=shift).count(), 1)


class ShiftVisibilityTests(TestCase):
    """Drafts must stay invisible to employees until they are published."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.barista = Position.objects.create(name="Barista")
        cls.manager = User.objects.create_user(
            username="manager2@example.com", password="x", role=UserRole.MANAGER
        )
        cls.alice = User.objects.create_user(
            username="alice2@example.com", password="x", role=UserRole.EMPLOYEE, position=cls.barista
        )
        cls.day = date(2030, 6, 3)
        cls.shift = Shift.objects.create(
            date=cls.day,
            start_time=time(9, 0),
            end_time=time(17, 0),
            capacity=1,
            position=cls.barista,
            created_by=cls.manager,
        )
        assign_employees_to_shift(cls.shift, [cls.alice.id])

    def _visible(self):
        return shifts_for_employee(
            employee_id=self.alice.id,
            start=self.day - timedelta(days=1),
            end=self.day + timedelta(days=1),
        )

    def test_draft_shift_is_hidden_from_employee(self):
        self.assertEqual(self._visible().count(), 0)

    def test_published_shift_is_visible_to_employee(self):
        self.shift.status = "published"
        self.shift.save(update_fields=["status"])
        self.assertEqual(self._visible().count(), 1)


class SearchAndAnalyticsTests(TestCase):
    """Search and analytics read only the signed-in manager's own shifts."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.barista = Position.objects.create(name="Barista")
        cls.chef = Position.objects.create(name="Head Chef")
        cls.manager = User.objects.create_user(username="manager3@example.com", password="x", role=UserRole.MANAGER)
        other_manager = User.objects.create_user(username="other3@example.com", password="x", role=UserRole.MANAGER)
        cls.alice = User.objects.create_user(
            username="alice3@example.com", password="x", role=UserRole.EMPLOYEE, position=cls.barista,
            first_name="Alice", last_name="Novak",
        )
        cls.bob = User.objects.create_user(
            username="bob3@example.com", password="x", role=UserRole.EMPLOYEE, position=cls.barista,
            first_name="Bob", last_name="Marek",
        )
        cls.barista_shift = cls._shift(cls.manager, cls.barista, time(9, 0), time(17, 0), 2, [cls.alice, cls.bob])
        cls.chef_shift = cls._shift(cls.manager, cls.chef, time(10, 0), time(14, 0), 1, [])
        # Another manager's shift with the same worker must never show up.
        cls._shift(other_manager, cls.barista, time(9, 0), time(17, 0), 1, [cls.alice])

    @classmethod
    def _shift(cls, manager, position, start, end, capacity, employees) -> Shift:
        shift = Shift.objects.create(
            date=timezone.localdate(), start_time=start, end_time=end, capacity=capacity,
            position=position, created_by=manager,
        )
        Assignment.objects.bulk_create([Assignment(shift=shift, employee=employee) for employee in employees])
        return shift

    def setUp(self) -> None:
        self.client.force_login(self.manager)

    def _search(self, **params) -> dict:
        return self.client.get(reverse("manager_shift_search"), params).context["bootstrap"]["data"]

    def _result_ids(self, **params) -> list[int]:
        return [row["id"] for row in self._search(**params)["results"]]

    def test_text_query_matches_worker_names(self):
        self.assertEqual(self._result_ids(q="novak"), [self.barista_shift.id])

    def test_text_query_matches_positions(self):
        self.assertEqual(self._result_ids(q="chef"), [self.chef_shift.id])

    def test_filters_combine(self):
        self.assertEqual(self._result_ids(position=self.barista.id, worker=self.bob.id), [self.barista_shift.id])
        self.assertEqual(self._result_ids(status="published"), [])

    def test_sorting_by_position_descending(self):
        self.assertEqual(self._result_ids(sort="position", dir="desc"), [self.chef_shift.id, self.barista_shift.id])

    def test_pagination(self):
        Shift.objects.bulk_create(
            Shift(date=timezone.localdate(), start_time=time(6, 0), end_time=time(7, 0), position=self.chef, created_by=self.manager)
            for _ in range(28)
        )
        data = self._search(page=2)
        self.assertEqual((data["total"], data["page"], data["totalPages"], len(data["results"])), (30, 2, 2, 5))

    def test_analytics_worker_filter_counts_only_that_worker(self):
        url = reverse("manager_analytics")
        everyone = self.client.get(url, {"format": "json"}).json()["analytics"]["kpis"]
        alice_only = self.client.get(url, {"format": "json", "worker": self.alice.id}).json()["analytics"]["kpis"]

        self.assertEqual(everyone, {"shifts": 2, "hours": 16.0, "workers": 2, "open_shifts": 1})
        self.assertEqual(alice_only, {"shifts": 1, "hours": 8.0, "workers": 1, "open_shifts": 0})

    def test_csv_export_lists_each_shift(self):
        response = self.client.get(reverse("manager_analytics_export_csv"))

        self.assertEqual(response["Content-Type"], "text/csv")
        lines = response.content.decode().strip().splitlines()
        self.assertEqual(len(lines), 3)
        self.assertIn("Alice Novak; Bob Marek", lines[1])


class ShiftVersionTests(TestCase):
    """A save from a form opened before someone else's edit is refused instead of overwriting it."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.barista = Position.objects.create(name="Barista")
        cls.manager = User.objects.create_user(username="manager@example.com", password="x", role=UserRole.MANAGER)
        cls.day = timezone.localdate() + timedelta(days=3)

    def setUp(self) -> None:
        self.shift = Shift.objects.create(
            date=self.day, start_time=time(9, 0), end_time=time(17, 0), position=self.barista, created_by=self.manager
        )
        self.client.force_login(self.manager)

    def _save(self, version: int, start: str):
        data = {"date": self.day.isoformat(), "start_time": start, "end_time": "17:00", "position": self.barista.id}
        return self.client.post(reverse("update_shift", args=[self.shift.id]), {**data, "capacity": 1, "version": version})

    def test_save_on_the_current_version_bumps_it(self):
        self._save(1, "10:00")

        self.shift.refresh_from_db()
        self.assertEqual((self.shift.start_time, self.shift.version), (time(10, 0), 2))

    def test_save_on_a_stale_version_is_refused(self):
        self._save(1, "10:00")
        response = self._save(1, "11:00")

        self.shift.refresh_from_db()
        self.assertEqual((self.shift.start_time, self.shift.version), (time(10, 0), 2))
        self.assertIn(STALE_SHIFT, [message.message for message in get_messages(response.wsgi_request)])


class CalendarViewTests(TestCase):
    """The manager calendar shows a month or a Monday-to-Sunday week, and remembers the choice."""

    @classmethod
    def setUpTestData(cls) -> None:
        barista = Position.objects.create(name="Barista")
        cls.manager = User.objects.create_user(username="manager@example.com", password="x", role=UserRole.MANAGER)
        # A Wednesday, and a day two weeks later in the same month.
        for day in (date(2030, 6, 5), date(2030, 6, 19)):
            Shift.objects.create(date=day, start_time=time(9, 0), end_time=time(17, 0), position=barista, created_by=cls.manager)

    def setUp(self) -> None:
        self.client.force_login(self.manager)

    def _data(self, **params) -> dict:
        return self.client.get(reverse("manager_shifts"), {"format": "json", "date": "2030-06-05", **params}).json()

    def test_week_view_shows_monday_to_sunday(self):
        data = self._data(view="week")

        self.assertEqual((data["view"], data["start"], data["end"]), ("week", "2030-06-03", "2030-06-09"))
        self.assertEqual([shift["date"] for shift in data["shifts"]], ["2030-06-05"])

    def test_the_last_chosen_view_is_remembered(self):
        self._data(view="week")
        self.assertEqual(self._data()["view"], "week")

        self.assertEqual(len(self._data(view="month")["shifts"]), 2)
        self.assertEqual(self._data()["view"], "month")
