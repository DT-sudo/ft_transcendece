from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.scheduling.models import Position

from .forms import SignUpForm
from .models import UserRole

User = get_user_model()


class SignUpTests(TestCase):
    """Public registration: email + password, hashed, with the server validating."""

    def _payload(self, **overrides) -> dict:
        payload = {
            "full_name": "Jane Doe",
            "email": "Jane.Doe@Example.com",
            "password1": "correct-horse-42",
            "password2": "correct-horse-42",
        }
        payload.update(overrides)
        return payload

    def test_signup_creates_a_manager_and_logs_them_in(self):
        response = self.client.post(reverse("signup"), self._payload(), follow=True)

        user = User.objects.get(email="jane.doe@example.com")
        self.assertEqual(user.role, UserRole.MANAGER)
        self.assertEqual(user.first_name, "Jane")
        self.assertEqual(user.last_name, "Doe")
        # username mirrors the email so both auth backends resolve the same user
        self.assertEqual(user.username, "jane.doe@example.com")
        self.assertEqual(response.wsgi_request.user, user)

    def test_signup_never_stores_the_raw_password(self):
        self.client.post(reverse("signup"), self._payload())

        user = User.objects.get(email="jane.doe@example.com")
        self.assertNotIn("correct-horse-42", user.password)
        self.assertTrue(user.password.startswith("pbkdf2_"))
        self.assertTrue(user.check_password("correct-horse-42"))

    def test_email_is_normalised_and_must_be_unique(self):
        self.client.post(reverse("signup"), self._payload())

        # Same address, different casing: the server must still reject it.
        form = SignUpForm(self._payload(email="JANE.DOE@example.com"))
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertEqual(User.objects.filter(email="jane.doe@example.com").count(), 1)

    def test_mismatched_passwords_are_rejected(self):
        form = SignUpForm(self._payload(password2="something-else-99"))
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_weak_passwords_are_rejected_by_django_validators(self):
        weak = {
            "short7": "too short",
            "12345678901": "entirely numeric",
            "password123": "too common",
            # similarity is only detected because _post_clean populates the
            # instance's username/name before running the validators
            "jane.doe@example.com": "too similar to the account details",
        }
        for password, reason in weak.items():
            with self.subTest(reason=reason):
                form = SignUpForm(self._payload(password1=password, password2=password))
                self.assertFalse(form.is_valid())
                # Django's creation form reports password-strength errors on the confirm field.
                self.assertIn("password2", form.errors)

    def test_signup_page_reports_field_errors_back_to_the_client(self):
        response = self.client.post(reverse("signup"), self._payload(email="not-an-email"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["bootstrap"]["data"]["fieldErrors"])
        self.assertFalse(User.objects.filter(first_name="Jane").exists())

    def test_signed_in_user_is_redirected_away_from_signup(self):
        self.client.post(reverse("signup"), self._payload())
        response = self.client.get(reverse("signup"))
        self.assertRedirects(response, reverse("home"), target_status_code=302)


class EmailLoginTests(TestCase):
    """Login is by email address (username mirrors the lowercased email)."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.password = "correct-horse-42"
        cls.user = User.objects.create_user(
            username="sam@example.com",
            email="sam@example.com",
            password=cls.password,
            role=UserRole.MANAGER,
        )

    def test_login_with_email_succeeds(self):
        response = self.client.post(
            reverse("login"), {"username": "sam@example.com", "password": self.password}
        )
        self.assertRedirects(response, reverse("home"), target_status_code=302)

    def test_login_email_is_case_insensitive(self):
        response = self.client.post(
            reverse("login"), {"username": "SAM@Example.com", "password": self.password}
        )
        self.assertRedirects(response, reverse("home"), target_status_code=302)

    def test_wrong_password_is_rejected_without_leaking_which_field_failed(self):
        response = self.client.post(
            reverse("login"), {"username": "sam@example.com", "password": "wrong-password-1"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertEqual(
            response.context["bootstrap"]["data"]["error"], "Incorrect email or password."
        )

    def test_unknown_email_is_rejected(self):
        response = self.client.post(
            reverse("login"), {"username": "nobody@example.com", "password": self.password}
        )
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_inactive_account_cannot_log_in(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])

        response = self.client.post(
            reverse("login"), {"username": "sam@example.com", "password": self.password}
        )
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class EmployeeFormValidationTests(TestCase):
    """The manager-side employee form validates on the server, not only in the browser."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.position = Position.objects.create(name="Barista")
        cls.manager = User.objects.create_user(
            username="boss@example.com",
            email="boss@example.com",
            password="correct-horse-42",
            role=UserRole.MANAGER,
        )

    def setUp(self) -> None:
        self.client.force_login(self.manager)

    def _create(self, **overrides):
        payload = {
            "full_name": "Pat Smith",
            "email": "pat@example.com",
            "position": self.position.id,
        }
        payload.update(overrides)
        return self.client.post(reverse("manager_employees_create"), payload, follow=True)

    def test_valid_employee_is_created_with_a_hashed_generated_password(self):
        self._create()

        employee = User.objects.get(email="pat@example.com")
        self.assertEqual(employee.role, UserRole.EMPLOYEE)
        self.assertTrue(employee.password.startswith("pbkdf2_"))

    def test_invalid_email_is_rejected_server_side(self):
        # A client that bypasses the browser validation must still be refused.
        self._create(email="definitely-not-an-email")
        self.assertFalse(User.objects.filter(first_name="Pat").exists())

    def test_missing_position_is_rejected_server_side(self):
        self._create(position="")
        self.assertFalse(User.objects.filter(first_name="Pat").exists())

    def test_duplicate_email_is_rejected(self):
        self._create()
        self._create(full_name="Other Person")

        self.assertEqual(User.objects.filter(email="pat@example.com").count(), 1)


class LegalPageTests(TestCase):
    """Privacy Policy and Terms of Service are public and are not placeholders."""

    def test_pages_are_reachable_without_logging_in(self):
        for name in ("privacy_policy", "terms_of_service"):
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)

    def test_pages_carry_real_content(self):
        for name in ("privacy_policy", "terms_of_service"):
            with self.subTest(page=name):
                document = self.client.get(reverse(name)).context["bootstrap"]["data"]["document"]

                self.assertTrue(document["title"])
                self.assertGreaterEqual(len(document["sections"]), 8)
                for section in document["sections"]:
                    self.assertTrue(section["heading"])
                    self.assertTrue(section.get("paragraphs") or section.get("bullets"))

    def test_every_page_links_to_both_documents(self):
        urls = self.client.get(reverse("login")).context["bootstrap"]["urls"]

        self.assertEqual(urls["privacy"], reverse("privacy_policy"))
        self.assertEqual(urls["terms"], reverse("terms_of_service"))
