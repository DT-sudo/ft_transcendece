from __future__ import annotations

import json
from datetime import date, time

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from apps.scheduling.models import Assignment, EmployeeUnavailability, Shift, ShiftStatus
from apps.accounts.models import Position, UserRole

User = get_user_model()


class PrivacyCenterAccessTests(TestCase):
    """The privacy center is a signed-in self-service page, not a public one."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.employee = User.objects.create_user(
            username="employee@example.com",
            email="employee@example.com",
            password="correct-horse-42",
            role=UserRole.EMPLOYEE,
        )

    def test_anonymous_visitor_is_redirected_to_login(self):
        for name in ("privacy_center", "privacy_export_data"):
            with self.subTest(view=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("login"), response.url)

    def test_signed_in_user_can_reach_the_privacy_center(self):
        self.client.force_login(self.employee)
        response = self.client.get(reverse("privacy_center"))

        self.assertEqual(response.status_code, 200)
        data = response.context["bootstrap"]["data"]
        self.assertEqual(data["email"], self.employee.email)
        self.assertEqual(data["urls"]["exportData"], reverse("privacy_export_data"))
        self.assertEqual(data["urls"]["deleteAccount"], reverse("privacy_delete_account"))


class ExportMyDataTests(TestCase):
    """The data export must be a complete, readable copy of what's held - and must notify."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.position = Position.objects.create(name="Barista")
        cls.manager = User.objects.create_user(
            username="manager@example.com",
            email="manager@example.com",
            password="correct-horse-42",
            role=UserRole.MANAGER,
        )
        cls.employee = User.objects.create_user(
            username="employee@example.com",
            email="employee@example.com",
            password="correct-horse-42",
            role=UserRole.EMPLOYEE,
            position=cls.position,
        )
        cls.shift = Shift.objects.create(
            date=date(2026, 9, 20),
            start_time=time(9, 0),
            end_time=time(13, 0),
            position=cls.position,
            status=ShiftStatus.PUBLISHED,
            created_by=cls.manager,
        )
        Assignment.objects.create(shift=cls.shift, employee=cls.employee)
        EmployeeUnavailability.objects.create(employee=cls.employee, date=date(2026, 9, 25))

    def test_employee_export_contains_their_shifts_and_unavailability(self):
        self.client.force_login(self.employee)
        response = self.client.get(reverse("privacy_export_data"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertIn("attachment", response["Content-Disposition"])

        payload = json.loads(response.content)
        self.assertEqual(payload["account"]["email"], self.employee.email)
        self.assertEqual(len(payload["assigned_shifts"]), 1)
        self.assertEqual(payload["assigned_shifts"][0]["position"], "Barista")
        self.assertEqual(payload["unavailability"], ["2026-09-25"])
        self.assertNotIn("shifts_created", payload)

    def test_manager_export_contains_shifts_they_created_not_assignments(self):
        self.client.force_login(self.manager)
        payload = json.loads(self.client.get(reverse("privacy_export_data")).content)

        self.assertEqual(len(payload["shifts_created"]), 1)
        self.assertEqual(payload["shifts_created"][0]["position"], "Barista")
        self.assertNotIn("assigned_shifts", payload)

    def test_export_sends_a_confirmation_email_to_the_account_owner(self):
        self.client.force_login(self.employee)
        self.client.get(reverse("privacy_export_data"))

        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertEqual(sent.to, [self.employee.email])
        self.assertIn("data export", sent.subject.lower())

    def test_a_flaky_mail_backend_does_not_break_the_download(self):
        """`fail_silently=True`: the export already happened, so a mail error must not surface."""
        with self.settings(EMAIL_BACKEND="django.core.mail.backends.dummy.EmailBackend"):
            self.client.force_login(self.employee)
            response = self.client.get(reverse("privacy_export_data"))

        self.assertEqual(response.status_code, 200)


class DeleteMyAccountTests(TestCase):
    """Self-service erasure: requires re-entering credentials, then is irreversible."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.password = "correct-horse-42"

    def setUp(self) -> None:
        self.position = Position.objects.create(name="Barista")
        self.employee = User.objects.create_user(
            username="employee@example.com",
            email="employee@example.com",
            password=self.password,
            role=UserRole.EMPLOYEE,
            position=self.position,
        )
        self.client.force_login(self.employee)

    def _delete(self, **overrides):
        payload = {"confirm_email": self.employee.email, "confirm_password": self.password}
        payload.update(overrides)
        return self.client.post(reverse("privacy_delete_account"), payload, follow=True)

    def test_correct_confirmation_deletes_the_account_and_logs_out(self):
        response = self._delete()

        self.assertFalse(User.objects.filter(email="employee@example.com").exists())
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertRedirects(response, reverse("login"))

    def test_wrong_password_refuses_and_keeps_the_account(self):
        response = self._delete(confirm_password="not-the-password")

        self.assertTrue(User.objects.filter(email="employee@example.com").exists())
        self.assertRedirects(response, reverse("privacy_center"))

    def test_mismatched_email_refuses_and_keeps_the_account(self):
        response = self._delete(confirm_email="someone-else@example.com")

        self.assertTrue(User.objects.filter(email="employee@example.com").exists())
        self.assertRedirects(response, reverse("privacy_center"))

    def test_confirmation_is_not_case_sensitive_on_email(self):
        self._delete(confirm_email="EMPLOYEE@EXAMPLE.com")
        self.assertFalse(User.objects.filter(email="employee@example.com").exists())

    def test_successful_deletion_sends_a_confirmation_email(self):
        self._delete()

        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertEqual(sent.to, ["employee@example.com"])
        self.assertIn("deleted", sent.subject.lower())

    def _manager_with_a_shift(self) -> tuple[User, Shift]:
        manager = User.objects.create_user(
            username="manager@example.com",
            email="manager@example.com",
            password=self.password,
            role=UserRole.MANAGER,
        )
        shift = Shift.objects.create(
            date=date(2026, 9, 20),
            start_time=time(9, 0),
            end_time=time(13, 0),
            position=self.position,
            created_by=manager,
        )
        return manager, shift

    def test_manager_who_created_shifts_can_self_delete_and_the_shifts_stay(self):
        """The schedule is shared: a manager's erasure unlinks the shifts they wrote, it doesn't remove them."""
        manager, shift = self._manager_with_a_shift()
        self.client.force_login(manager)

        response = self.client.post(
            reverse("privacy_delete_account"),
            {"confirm_email": manager.email, "confirm_password": self.password},
            follow=True,
        )

        self.assertFalse(User.objects.filter(email="manager@example.com").exists())
        self.assertRedirects(response, reverse("login"))
        shift.refresh_from_db()
        self.assertIsNone(shift.created_by)
        self.assertEqual(len(mail.outbox), 1)

    def test_deleting_own_account_removes_assignments_and_unavailability(self):
        _, shift = self._manager_with_a_shift()
        Assignment.objects.create(shift=shift, employee=self.employee)
        EmployeeUnavailability.objects.create(employee=self.employee, date=date(2026, 9, 25))

        self._delete()

        self.assertFalse(Assignment.objects.filter(shift=shift).exists())
        self.assertFalse(EmployeeUnavailability.objects.exists())
