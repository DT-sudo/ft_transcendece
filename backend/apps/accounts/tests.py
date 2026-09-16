from __future__ import annotations

from datetime import date, time
from io import StringIO

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.scheduling.management.commands.seed_demo import DEMO_EMPLOYEE_EMAIL, DEMO_MANAGER_EMAIL
from apps.scheduling.models import Shift

from .forms import SignUpForm
from .models import MANAGER_POSITION_NAME, Position, UserRole

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


@override_settings(ENABLE_DEMO_LOGIN=True)
class DemoLoginTests(TestCase):
    """One-click demo buttons sign in as the seeded accounts, and only while enabled."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.manager = User.objects.create_user(
            username=DEMO_MANAGER_EMAIL, email=DEMO_MANAGER_EMAIL, role=UserRole.MANAGER
        )
        cls.employee = User.objects.create_user(
            username=DEMO_EMPLOYEE_EMAIL, email=DEMO_EMPLOYEE_EMAIL, role=UserRole.EMPLOYEE
        )

    def test_login_page_offers_both_buttons(self):
        data = self.client.get(reverse("login")).context["bootstrap"]["data"]

        self.assertTrue(data["showDemo"])
        self.assertEqual(data["urls"]["demoManager"], reverse("demo_login", args=["manager"]))
        self.assertEqual(data["urls"]["demoEmployee"], reverse("demo_login", args=["employee"]))

    def test_each_button_signs_in_as_its_role(self):
        for role, user in (("manager", self.manager), ("employee", self.employee)):
            with self.subTest(role=role):
                self.client.logout()
                response = self.client.get(reverse("demo_login", args=[role]))

                self.assertRedirects(response, reverse("home"), target_status_code=302)
                self.assertEqual(response.wsgi_request.user, user)

    def test_missing_demo_accounts_do_not_sign_anyone_in(self):
        User.objects.filter(username=DEMO_MANAGER_EMAIL).delete()
        response = self.client.get(reverse("demo_login", args=["manager"]))

        self.assertRedirects(response, reverse("login"))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    @override_settings(ENABLE_DEMO_LOGIN=False)
    def test_disabled_demo_login_hides_the_buttons_and_refuses(self):
        data = self.client.get(reverse("login")).context["bootstrap"]["data"]
        self.assertFalse(data["showDemo"])
        self.assertNotIn("demoManager", data["urls"])

        response = self.client.get(reverse("demo_login", args=["manager"]))
        self.assertRedirects(response, reverse("login"))
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class AccountFormValidationTests(TestCase):
    """The admin's account form validates on the server, not only in the browser."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.position = Position.objects.create(name="Barista")
        cls.admin = User.objects.create_user(
            username="boss@example.com",
            email="boss@example.com",
            password="correct-horse-42",
            role=UserRole.ADMIN,
        )

    def setUp(self) -> None:
        self.client.force_login(self.admin)

    def _create(self, **overrides):
        payload = {
            "full_name": "Pat Smith",
            "email": "pat@example.com",
            "role": UserRole.EMPLOYEE,
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


class EmployeeDeleteGdprTests(TestCase):
    """Admin-initiated erasure is the other door to the same GDPR right that
    apps.privacy's self-service delete exercises, and must close the same way:
    a confirmation email to the person whose data was erased."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.position = Position.objects.create(name="Barista")
        cls.admin = User.objects.create_user(
            username="boss@example.com",
            email="boss@example.com",
            password="correct-horse-42",
            role=UserRole.ADMIN,
        )
        cls.employee = User.objects.create_user(
            username="pat@example.com",
            email="pat@example.com",
            first_name="Pat",
            last_name="Smith",
            role=UserRole.EMPLOYEE,
            position=cls.position,
        )

    def setUp(self) -> None:
        self.client.force_login(self.admin)

    def test_delete_removes_the_employee(self):
        self.client.post(reverse("employee_delete", args=[self.employee.id]), follow=True)
        self.assertFalse(User.objects.filter(email="pat@example.com").exists())

    def test_delete_sends_a_confirmation_email_to_the_employee_not_the_admin(self):
        self.client.post(reverse("employee_delete", args=[self.employee.id]), follow=True)

        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertEqual(sent.to, ["pat@example.com"])
        self.assertIn("deleted", sent.subject.lower())
        self.assertIn("Pat Smith", sent.body)

    def test_a_flaky_mail_backend_does_not_block_the_deletion(self):
        with self.settings(EMAIL_BACKEND="django.core.mail.backends.dummy.EmailBackend"):
            response = self.client.post(
                reverse("employee_delete", args=[self.employee.id]), follow=True
            )

        self.assertFalse(User.objects.filter(email="pat@example.com").exists())
        self.assertEqual(response.status_code, 200)


class RolePermissionTests(TestCase):
    """Admins provision every account, its role and the positions; managers only run the schedule."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.position = Position.objects.create(name="Barista")
        cls.admin = User.objects.create_user(username="admin@example.com", email="admin@example.com", role=UserRole.ADMIN)
        cls.manager = User.objects.create_user(username="boss@example.com", email="boss@example.com", role=UserRole.MANAGER)
        cls.employee = User.objects.create_user(
            username="pat@example.com", email="pat@example.com", role=UserRole.EMPLOYEE, position=cls.position
        )

    def _team(self, user) -> dict:
        self.client.force_login(user)
        return self.client.get(reverse("manager_employees")).context["bootstrap"]["data"]

    def _update(self, user, target, **fields):
        self.client.force_login(user)
        data = {
            "full_name": "Some Name",
            "email": target.email,
            "role": target.role,
            "position": target.position_id or "",
            **fields,
        }
        return self.client.post(reverse("employee_update", args=[target.id]), data)

    def _shift_by(self, manager) -> None:
        Shift.objects.create(
            date=date(2030, 6, 3), start_time=time(9, 0), end_time=time(17, 0), position=self.position, created_by=manager
        )

    def test_admin_sees_every_other_account_and_the_roles(self):
        data = self._team(self.admin)

        self.assertEqual({row["email"] for row in data["employees"]}, {"boss@example.com", "pat@example.com"})
        self.assertEqual([role["id"] for role in data["roles"]], ["admin", "manager", "employee"])

    def test_managers_have_no_account_management_at_all(self):
        """Provisioning accounts and positions is the admin's job; a manager is sent back to the schedule."""
        self.client.force_login(self.manager)
        pages = (
            ("manager_employees", ()),
            ("manager_employees_create", ()),
            ("employee_update", (self.employee.id,)),
            ("employee_delete", (self.employee.id,)),
            ("reset_employee_password", (self.employee.id,)),
            ("reset_employee_two_factor", (self.employee.id,)),
            ("position_create", ()),
            ("position_delete", (self.position.id,)),
        )
        for name, args in pages:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url) if not args and name == "manager_employees" else self.client.post(url)
                self.assertRedirects(response, reverse("manager_shifts"))
        self.assertTrue(User.objects.filter(pk=self.employee.pk).exists())
        self.assertTrue(Position.objects.filter(pk=self.position.pk).exists())

    def test_admin_changes_a_role(self):
        self._update(self.admin, self.employee, role=UserRole.MANAGER)

        self.employee.refresh_from_db()
        self.assertEqual((self.employee.role, self.employee.position), (UserRole.MANAGER, None))

    def test_admin_creates_a_manager_but_an_employee_needs_a_position(self):
        self.client.force_login(self.admin)
        url = reverse("manager_employees_create")
        self.client.post(url, {"full_name": "New Boss", "email": "new@example.com", "role": UserRole.MANAGER})
        self.client.post(url, {"full_name": "No Post", "email": "nopost@example.com", "role": UserRole.EMPLOYEE})

        self.assertEqual(User.objects.get(email="new@example.com").role, UserRole.MANAGER)
        self.assertFalse(User.objects.filter(email="nopost@example.com").exists())

    def test_employees_have_no_account_management_either(self):
        self.client.force_login(self.employee)
        self.assertRedirects(self.client.get(reverse("manager_employees")), reverse("employee_shifts"))

    def test_admin_cannot_manage_their_own_account(self):
        self.assertEqual(self._update(self.admin, self.admin, role=UserRole.EMPLOYEE).status_code, 404)

    def test_role_switch_that_would_strand_shifts_is_refused(self):
        self._shift_by(self.manager)

        self._update(self.admin, self.manager, role=UserRole.EMPLOYEE, position=self.position.id)

        self.manager.refresh_from_db()
        self.assertEqual(self.manager.role, UserRole.MANAGER)

    def test_manager_with_shifts_cannot_be_deleted(self):
        self._shift_by(self.manager)
        self.client.force_login(self.admin)

        self.client.post(reverse("employee_delete", args=[self.manager.id]))

        self.assertTrue(User.objects.filter(pk=self.manager.pk).exists())

    def test_admin_does_not_run_the_schedule(self):
        """Admins only manage accounts: shifts, search and analytics are a manager's job."""
        self.client.force_login(self.admin)
        for name in ("manager_shifts", "manager_shift_search", "manager_analytics"):
            with self.subTest(name=name):
                self.assertRedirects(self.client.get(reverse(name)), reverse("manager_employees"))

    def test_picking_the_manager_position_promotes_the_employee(self):
        manager_position = Position.objects.get(name=MANAGER_POSITION_NAME)

        self._update(self.admin, self.employee, position=manager_position.id)

        self.employee.refresh_from_db()
        self.assertEqual((self.employee.role, self.employee.position), (UserRole.MANAGER, None))

    def test_promoting_an_employee_with_shifts_is_refused(self):
        manager_position = Position.objects.get(name=MANAGER_POSITION_NAME)
        Shift.objects.create(
            date=date(2030, 6, 3), start_time=time(9, 0), end_time=time(17, 0), position=self.position, created_by=self.manager
        ).assignments.create(employee=self.employee)

        self._update(self.admin, self.employee, position=manager_position.id)

        self.employee.refresh_from_db()
        self.assertEqual(self.employee.role, UserRole.EMPLOYEE)

    def test_the_manager_position_cannot_be_deleted(self):
        manager_position = Position.objects.get(name=MANAGER_POSITION_NAME)
        self.client.force_login(self.admin)

        self.client.post(reverse("position_delete", args=[manager_position.id]))

        self.assertTrue(Position.objects.filter(pk=manager_position.pk).exists())

    def test_make_admin_command_promotes_an_account(self):
        call_command("make_admin", "BOSS@example.com", stdout=StringIO())

        self.manager.refresh_from_db()
        self.assertEqual(self.manager.role, UserRole.ADMIN)


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
