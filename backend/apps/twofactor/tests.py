from __future__ import annotations

import base64
import json
import time
from datetime import timedelta

from django.core import mail
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Position, User, UserRole
from apps.notifications.models import Notification
from apps.scheduling.management.commands.seed_demo import DEMO_MANAGER_EMAIL

from . import services, totp
from .models import RecoveryCode, TOTPDevice
from .views import PENDING_LOGIN, SETUP_SECRET

PASSWORD = "correct-horse-42"
SETTINGS = reverse("account_settings")


def code_now(secret: str, offset: int = 0) -> str:
    return totp.code_at(secret, totp.current_step() + offset)


def wrong_code(secret: str) -> str:
    valid = {code_now(secret, offset) for offset in (-1, 0, 1, 2)}
    return next(code for code in (f"{n:06d}" for n in range(10**6)) if code not in valid)


class TotpTests(SimpleTestCase):
    """The algorithm against the published RFC 6238 test vectors (SHA-1, last 6 of the 8 digits)."""

    SECRET = base64.b32encode(b"12345678901234567890").decode()

    def test_rfc_6238_vectors(self):
        vectors = {59: "287082", 1111111109: "081804", 1111111111: "050471", 1234567890: "005924", 2000000000: "279037"}
        for timestamp, expected in vectors.items():
            with self.subTest(timestamp=timestamp):
                self.assertEqual(totp.code_at(self.SECRET, totp.current_step(timestamp)), expected)

    def test_window_accepts_one_step_either_side_only(self):
        now = 1111111109  # step 37037036
        step = totp.current_step(now)
        for offset in (-1, 0, 1):
            self.assertEqual(totp.matching_step(self.SECRET, totp.code_at(self.SECRET, step + offset), now=now), step + offset)
        for offset in (-2, 2):
            self.assertIsNone(totp.matching_step(self.SECRET, totp.code_at(self.SECRET, step + offset), now=now))

    def test_steps_up_to_after_are_refused(self):
        now = 1111111109
        step = totp.current_step(now)
        self.assertIsNone(totp.matching_step(self.SECRET, totp.code_at(self.SECRET, step), after=step, now=now))

    def test_secret_uri_and_qr_code(self):
        secret = totp.new_secret()
        self.assertEqual(len(base64.b32decode(secret)), 20)
        uri = totp.provisioning_uri(secret, "sam@example.com")
        self.assertTrue(uri.startswith("otpauth://totp/PlanShift%3Asam%40example.com?"))
        self.assertIn(f"secret={secret}", uri)
        self.assertIn("issuer=PlanShift", uri)
        self.assertTrue(totp.qr_data_uri(uri).startswith("data:image/svg+xml"))


class TwoFactorTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        barista = Position.objects.create(name="Barista")

        def make(name, role, position=None):
            email = f"{name}@example.com"
            return User.objects.create_user(
                username=email, email=email, password=PASSWORD, role=role, first_name=name.title(), position=position
            )

        cls.manager = make("maya", UserRole.MANAGER)
        cls.employee = make("sam", UserRole.EMPLOYEE, barista)
        cls.admin = make("ada", UserRole.ADMIN)

    def turn_on(self, user: User) -> tuple[str, list[str]]:
        secret = totp.new_secret()
        # An old step as "last used", so the current code is still available to sign in with.
        codes = services.enable(user, secret, totp.current_step() - 5)
        mail.outbox.clear()
        return secret, codes

    def sign_in(self, user: User, code: str | None = None, **extra):
        response = self.client.post(reverse("login"), {"username": user.email, "password": PASSWORD})
        if code is None:
            return response
        return self.client.post(reverse("login_verify"), {"code": code, **extra})

    def signed_in_as(self) -> int | None:
        user_id = self.client.session.get("_auth_user_id")
        return int(user_id) if user_id else None

    def settings_data(self) -> dict:
        return self.client.get(SETTINGS).context["bootstrap"]["data"]["twoFactor"]


class SetupTests(TwoFactorTestCase):
    def setUp(self) -> None:
        self.client.force_login(self.employee)

    def start(self) -> str:
        self.assertRedirects(self.client.post(SETTINGS, {"section": "2fa_start"}), SETTINGS + "#security", fetch_redirect_response=False)
        return self.client.session[SETUP_SECRET]

    def test_setup_shows_the_qr_code_and_a_confirmed_code_turns_it_on(self):
        self.assertFalse(self.settings_data()["enabled"])
        secret = self.start()

        setup = self.settings_data()["setup"]
        self.assertEqual(setup["secret"], secret)
        self.assertTrue(setup["qr"].startswith("data:image/svg+xml"))
        self.assertFalse(TOTPDevice.objects.exists())

        response = self.client.post(SETTINGS, {"section": "2fa_confirm", "code": wrong_code(secret)})
        self.assertEqual(response.status_code, 200)
        self.assertIn("code", response.context["bootstrap"]["data"]["twoFactor"]["errors"])
        self.assertFalse(TOTPDevice.objects.exists())

        response = self.client.post(SETTINGS, {"section": "2fa_confirm", "code": code_now(secret)})
        self.assertRedirects(response, SETTINGS + "#security", fetch_redirect_response=False)
        self.assertEqual(TOTPDevice.objects.get(user=self.employee).secret, secret)
        self.assertNotIn(SETUP_SECRET, self.client.session)

        # The recovery codes are shown exactly once, and only their hashes are stored.
        state = self.settings_data()
        self.assertTrue(state["enabled"])
        self.assertIsNone(state["setup"])
        self.assertEqual(len(state["recoveryCodes"]), services.RECOVERY_CODE_COUNT)
        self.assertEqual(state["recoveryCodesLeft"], services.RECOVERY_CODE_COUNT)
        hashes = set(RecoveryCode.objects.values_list("code_hash", flat=True))
        self.assertFalse(hashes & set(state["recoveryCodes"]))
        self.assertIsNone(self.settings_data()["recoveryCodes"])

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.employee.email])
        self.assertTrue(Notification.objects.filter(recipient=self.employee, title="Two-factor authentication turned on").exists())

    def test_the_code_that_confirmed_setup_cannot_sign_in(self):
        secret = self.start()
        code = code_now(secret)
        self.client.post(SETTINGS, {"section": "2fa_confirm", "code": code})
        self.client.logout()

        self.sign_in(self.employee, code)
        self.assertIsNone(self.signed_in_as())

    def test_cancel_forgets_the_secret(self):
        self.start()
        self.client.post(SETTINGS, {"section": "2fa_cancel"})
        self.assertNotIn(SETUP_SECRET, self.client.session)
        self.assertIsNone(self.settings_data()["setup"])

    def test_confirm_without_a_started_setup_changes_nothing(self):
        self.client.post(SETTINGS, {"section": "2fa_confirm", "code": "123456"})
        self.assertFalse(TOTPDevice.objects.exists())


class LoginTests(TwoFactorTestCase):
    def test_without_2fa_the_password_signs_in_directly(self):
        response = self.sign_in(self.manager)
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        self.assertEqual(self.signed_in_as(), self.manager.pk)

    def test_password_leads_to_the_code_step_and_the_code_signs_in(self):
        secret, _ = self.turn_on(self.manager)

        response = self.sign_in(self.manager)
        self.assertRedirects(response, reverse("login_verify"), fetch_redirect_response=False)
        self.assertIsNone(self.signed_in_as())

        page = self.client.get(reverse("login_verify"))
        self.assertEqual(page.context["bootstrap"]["page"], "two-factor-verify")
        self.assertIsNone(self.signed_in_as())
        # Nothing behind the login is reachable in between.
        self.assertRedirects(self.client.get(reverse("account_settings")), f"{reverse('login')}?next={SETTINGS}", fetch_redirect_response=False)

        response = self.client.post(reverse("login_verify"), {"code": code_now(secret)})
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        self.assertEqual(self.signed_in_as(), self.manager.pk)
        self.assertNotIn(PENDING_LOGIN, self.client.session)

    def test_a_wrong_code_is_refused_in_place(self):
        secret, _ = self.turn_on(self.manager)
        response = self.sign_in(self.manager, wrong_code(secret))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["bootstrap"]["data"]["error"], "That code is not valid. Try again.")
        self.assertIsNone(self.signed_in_as())

    def test_a_used_code_cannot_be_replayed(self):
        secret, _ = self.turn_on(self.manager)
        code = code_now(secret)
        self.sign_in(self.manager, code)
        self.assertEqual(self.signed_in_as(), self.manager.pk)
        self.client.logout()

        self.sign_in(self.manager, code)
        self.assertIsNone(self.signed_in_as())

    def test_a_recovery_code_works_once_in_any_format(self):
        _, codes = self.turn_on(self.manager)
        response = self.sign_in(self.manager, codes[0].replace("-", " ").upper(), mode="recovery")

        self.assertEqual(self.signed_in_as(), self.manager.pk)
        self.assertEqual(services.recovery_codes_left(self.manager), services.RECOVERY_CODE_COUNT - 1)
        self.assertIn("recovery code", next(iter(response.wsgi_request._messages)).message)
        self.client.logout()

        self.sign_in(self.manager, codes[0])
        self.assertIsNone(self.signed_in_as())

    def test_five_wrong_codes_lock_the_check_for_five_minutes(self):
        secret, _ = self.turn_on(self.manager)
        self.sign_in(self.manager)
        for _ in range(services.MAX_FAILED_ATTEMPTS - 1):
            self.assertEqual(self.client.post(reverse("login_verify"), {"code": wrong_code(secret)}).status_code, 200)

        response = self.client.post(reverse("login_verify"), {"code": wrong_code(secret)})
        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)
        self.assertNotIn(PENDING_LOGIN, self.client.session)

        # Even the right password and the right code are refused until the lock ends.
        self.sign_in(self.manager, code_now(secret))
        self.assertIsNone(self.signed_in_as())

        TOTPDevice.objects.filter(user=self.manager).update(locked_until=timezone.now() - timedelta(seconds=1))
        self.sign_in(self.manager, code_now(secret))
        self.assertEqual(self.signed_in_as(), self.manager.pk)
        self.assertEqual(TOTPDevice.objects.get(user=self.manager).failed_attempts, 0)

    def test_the_code_step_expires(self):
        secret, _ = self.turn_on(self.manager)
        self.sign_in(self.manager)
        session = self.client.session
        session[PENDING_LOGIN] = {**session[PENDING_LOGIN], "started": time.time() - 301}
        session.save()

        response = self.client.post(reverse("login_verify"), {"code": code_now(secret)})
        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)
        self.assertIsNone(self.signed_in_as())

    def test_no_code_step_without_a_password_first(self):
        self.turn_on(self.manager)
        self.assertRedirects(self.client.get(reverse("login_verify")), reverse("login"), fetch_redirect_response=False)

    def test_cancel_drops_the_pending_sign_in(self):
        self.turn_on(self.manager)
        self.sign_in(self.manager)
        self.client.post(reverse("login_verify_cancel"))
        self.assertNotIn(PENDING_LOGIN, self.client.session)

    @override_settings(ENABLE_DEMO_LOGIN=True)
    def test_demo_login_asks_for_the_code_too(self):
        demo = User.objects.create_user(username=DEMO_MANAGER_EMAIL, email=DEMO_MANAGER_EMAIL, role=UserRole.MANAGER)
        secret, _ = self.turn_on(demo)

        response = self.client.get(reverse("demo_login", args=["manager"]))
        self.assertRedirects(response, reverse("login_verify"), fetch_redirect_response=False)
        self.assertIsNone(self.signed_in_as())

        self.client.post(reverse("login_verify"), {"code": code_now(secret)})
        self.assertEqual(self.signed_in_as(), demo.pk)


class ManageTests(TwoFactorTestCase):
    """Turning it off and replacing recovery codes take the password and a code."""

    def setUp(self) -> None:
        self.secret, self.codes = self.turn_on(self.employee)
        self.client.force_login(self.employee)

    def post(self, section: str, password: str = PASSWORD, code: str | None = None):
        return self.client.post(SETTINGS, {"section": section, "password": password, "code": code or code_now(self.secret)})

    def test_turning_off_needs_the_password(self):
        response = self.post("2fa_disable", password="wrong-password-1")

        self.assertIn("password", response.context["bootstrap"]["data"]["twoFactor"]["errors"])
        device = TOTPDevice.objects.get(user=self.employee)
        # A wrong password doesn't use up code attempts.
        self.assertEqual(device.failed_attempts, 0)

    def test_turning_off_needs_a_valid_code(self):
        response = self.post("2fa_disable", code=wrong_code(self.secret))
        self.assertIn("code", response.context["bootstrap"]["data"]["twoFactor"]["errors"])
        self.assertTrue(TOTPDevice.objects.filter(user=self.employee).exists())

    def test_turning_off_deletes_the_secret_and_codes_and_says_so(self):
        response = self.post("2fa_disable")

        self.assertRedirects(response, SETTINGS + "#security", fetch_redirect_response=False)
        self.assertFalse(TOTPDevice.objects.exists())
        self.assertFalse(RecoveryCode.objects.exists())
        self.assertEqual(len(mail.outbox), 1)
        self.client.logout()
        self.sign_in(self.employee)
        self.assertEqual(self.signed_in_as(), self.employee.pk)

    def test_a_recovery_code_can_turn_it_off(self):
        self.post("2fa_disable", code=self.codes[3])
        self.assertFalse(TOTPDevice.objects.exists())

    def test_new_recovery_codes_replace_the_old_ones(self):
        self.post("2fa_recovery")

        new_codes = self.settings_data()["recoveryCodes"]
        self.assertEqual(len(new_codes), services.RECOVERY_CODE_COUNT)
        self.assertFalse(set(new_codes) & set(self.codes))
        self.assertEqual(services.verify(self.employee, self.codes[0]), services.Result.INVALID)
        self.assertEqual(services.verify(self.employee, new_codes[0]), services.Result.RECOVERY_CODE)


class ResetByAdminTests(TwoFactorTestCase):
    def test_users_page_shows_who_uses_2fa(self):
        self.turn_on(self.employee)
        self.client.force_login(self.admin)
        employees = self.client.get(reverse("manager_employees")).context["bootstrap"]["data"]["employees"]
        self.assertEqual({e["id"]: e["twoFactor"] for e in employees}[self.employee.pk], True)

    def test_an_admin_can_reset_an_employee_and_the_employee_is_told(self):
        self.turn_on(self.employee)
        self.client.force_login(self.admin)
        self.client.post(reverse("reset_employee_two_factor", args=[self.employee.pk]))

        self.assertFalse(TOTPDevice.objects.filter(user=self.employee).exists())
        notice = Notification.objects.get(recipient=self.employee, title="Two-factor authentication reset")
        self.assertEqual(notice.actor, self.admin)
        self.assertEqual(mail.outbox[0].to, [self.employee.email])

    def test_an_admin_cannot_reset_their_own(self):
        self.turn_on(self.admin)
        self.client.force_login(self.admin)
        response = self.client.post(reverse("reset_employee_two_factor", args=[self.admin.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(TOTPDevice.objects.filter(user=self.admin).exists())

    def test_managers_and_employees_cannot_reset_anyone(self):
        self.turn_on(self.employee)
        for actor in (self.manager, self.employee):
            with self.subTest(actor=actor.role):
                self.client.force_login(actor)
                self.client.post(reverse("reset_employee_two_factor", args=[self.employee.pk]))
                self.assertTrue(TOTPDevice.objects.filter(user=self.employee).exists())


class ExportTests(TwoFactorTestCase):
    def test_the_data_export_says_2fa_is_on_but_never_holds_the_secret(self):
        secret, codes = self.turn_on(self.employee)
        self.client.force_login(self.employee)
        body = self.client.get(reverse("privacy_export_data")).content.decode()

        self.assertEqual(json.loads(body)["two_factor_authentication"]["enabled"], True)
        self.assertNotIn(secret, body)
        self.assertNotIn(codes[0], body)
