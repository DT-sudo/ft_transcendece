from __future__ import annotations

from urllib.parse import unquote

from django.conf import settings
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from apps.accounts.models import User, UserRole
from apps.notifications.models import Notification
from apps.notifications.services import notify, recent_notifications
from apps.scheduling.models import Position

PASSWORD = "correct-horse-42"
COOKIE = settings.LANGUAGE_COOKIE_NAME


class I18nTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.barista = Position.objects.create(name="Barista")

        def make(name, role, language=""):
            email = f"{name}@example.com"
            return User.objects.create_user(
                username=email,
                email=email,
                password=PASSWORD,
                role=role,
                first_name=name.title(),
                last_name="Test",
                language=language,
                position=cls.barista if role == UserRole.EMPLOYEE else None,
            )

        cls.manager = make("maya", UserRole.MANAGER, "en")
        cls.employee = make("sam", UserRole.EMPLOYEE, "cs")

    def tearDown(self) -> None:
        # Views activate languages on the test thread; don't let one leak into the next test.
        translation.activate(settings.LANGUAGE_CODE)

    def bootstrap(self, response) -> dict:
        return response.context["bootstrap"]


class LanguagePickTests(I18nTestCase):
    def test_english_left_to_right_by_default(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(self.bootstrap(response)["locale"], {"language": "en", "dir": "ltr"})
        self.assertContains(response, '<html lang="en" dir="ltr">')
        self.assertEqual([option["code"] for option in self.bootstrap(response)["languages"]], ["en", "cs", "ar"])

    def test_the_browser_language_is_used_for_visitors(self):
        response = self.client.get(reverse("login"), HTTP_ACCEPT_LANGUAGE="cs-CZ,cs;q=0.9")
        self.assertEqual(self.bootstrap(response)["locale"]["language"], "cs")

    def test_arabic_turns_the_page_right_to_left(self):
        self.client.cookies[COOKIE] = "ar"
        response = self.client.get(reverse("login"))
        self.assertEqual(self.bootstrap(response)["locale"], {"language": "ar", "dir": "rtl"})
        self.assertContains(response, '<html lang="ar" dir="rtl">')

    def test_a_signed_in_user_reads_their_saved_language_whatever_the_browser_says(self):
        self.client.force_login(self.employee)
        response = self.client.get(reverse("employee_shifts"), HTTP_ACCEPT_LANGUAGE="ar")
        self.assertEqual(self.bootstrap(response)["locale"]["language"], "cs")
        self.assertEqual(response.cookies[COOKIE].value, "cs")

    def test_an_account_without_a_language_keeps_the_detected_one(self):
        newcomer = User.objects.create_user(username="new@example.com", email="new@example.com", password=PASSWORD, role=UserRole.MANAGER)
        self.client.force_login(newcomer)
        self.client.get(reverse("manager_shifts"), HTTP_ACCEPT_LANGUAGE="ar")
        newcomer.refresh_from_db()
        self.assertEqual(newcomer.language, "ar")

    def test_a_language_picked_on_the_login_page_carries_into_the_account(self):
        self.client.cookies[COOKIE] = "ar"
        self.client.post(reverse("login"), {"username": self.manager.email, "password": PASSWORD})
        self.manager.refresh_from_db()
        self.assertEqual(self.manager.language, "ar")


class SwitchTests(I18nTestCase):
    def test_visitors_switch_with_a_cookie(self):
        response = self.client.post(reverse("set_language"), {"language": "ar"})
        self.assertEqual(response.json(), {"language": "ar", "dir": "rtl", "user": None})
        self.assertEqual(response.cookies[COOKIE].value, "ar")
        self.assertEqual(self.bootstrap(self.client.get(reverse("login")))["locale"]["language"], "ar")

    def test_signed_in_users_switch_on_their_account_and_get_their_card_translated(self):
        self.client.force_login(self.manager)
        response = self.client.post(reverse("set_language"), {"language": "cs"})
        self.manager.refresh_from_db()
        self.assertEqual(self.manager.language, "cs")
        self.assertEqual(response.json()["user"]["role"], "Manažer")

    def test_an_unknown_language_is_refused(self):
        response = self.client.post(reverse("set_language"), {"language": "xx"})
        self.assertEqual(response.status_code, 400)
        self.assertNotIn(COOKIE, response.cookies)

    def test_json_mode_carries_the_translated_page_title(self):
        self.client.force_login(self.employee)
        response = self.client.get(reverse("employee_shifts"), {"format": "json"})
        self.assertEqual(unquote(response["X-Page-Title"]), "Moje směny")


class ServerTextTests(I18nTestCase):
    def test_every_language_has_compiled_translations(self):
        # Fails when a .po file was edited without running `compilemessages`.
        for code, expected in (("cs", "Směna byla vytvořena."), ("ar", "تم إنشاء المناوبة.")):
            with self.subTest(language=code), translation.override(code):
                self.assertEqual(translation.gettext("Shift created."), expected)

    def test_flash_messages_and_form_errors_are_translated(self):
        self.client.cookies[COOKIE] = "cs"
        response = self.client.post(reverse("login"), {"username": self.manager.email, "password": "wrong-password-1"})
        self.assertEqual(self.bootstrap(response)["data"]["error"], "Nesprávný e-mail nebo heslo.")

        # Signed in, the account's saved language decides, so this manager reads Czech.
        User.objects.filter(pk=self.manager.pk).update(language="cs")
        self.client.force_login(self.manager)
        response = self.client.post(reverse("position_create"), {"name": ""}, follow=True)
        self.assertIn("Zadejte název pozice.", [message["text"] for message in self.bootstrap(response)["messages"]])

    def test_django_messages_come_translated_too(self):
        self.client.cookies[COOKIE] = "cs"
        response = self.client.post(
            reverse("signup"),
            {"full_name": "Jana Nová", "email": "jana@example.com", "password1": "12345678901", "password2": "12345678901"},
        )
        # Django ships its own Czech catalog for the password validators.
        self.assertIn("Heslo", self.bootstrap(response)["data"]["fieldErrors"]["password2"])

    def test_legal_documents_follow_the_language(self):
        for code, title in (("en", "Privacy Policy"), ("cs", "Zásady ochrany osobních údajů"), ("ar", "سياسة الخصوصية")):
            with self.subTest(language=code):
                self.client.cookies[COOKIE] = code
                document = self.bootstrap(self.client.get(reverse("privacy_policy")))["data"]["document"]
                self.assertEqual(document["title"], title)

    def test_legal_translations_have_the_same_structure(self):
        from apps.legal.documents import NAMES, TRANSLATIONS

        def shape(document):
            return [(len(section.get("paragraphs", [])), len(section.get("bullets", []))) for section in document["sections"]]

        for code, content in TRANSLATIONS.items():
            for name in NAMES:
                with self.subTest(language=code, document=name):
                    self.assertEqual(shape(content.DOCUMENTS[name]), shape(TRANSLATIONS["en"].DOCUMENTS[name]))
                    self.assertEqual(len(content.DOCUMENTS[name]["intro"]), len(TRANSLATIONS["en"].DOCUMENTS[name]["intro"]))


class RecipientLanguageTests(I18nTestCase):
    def test_a_notification_reads_in_whoever_reads_it(self):
        notify([self.employee], "friend.requested", actor=self.manager, name="Maya Test")
        notification = Notification.objects.get(recipient=self.employee)
        self.assertEqual(notification.title, "New friend request")  # the stored record is English

        for code, title in (("en", "New friend request"), ("cs", "Nová žádost o přátelství"), ("ar", "طلب صداقة جديد")):
            with self.subTest(language=code), translation.override(code):
                self.assertEqual(recent_notifications(self.employee)[0]["title"], title)

    def test_the_live_push_is_written_in_the_recipients_language_not_the_actors(self):
        from unittest import mock

        with mock.patch("apps.notifications.services.push_to_user") as push, translation.override("en"):
            notify([self.employee], "position.created", actor=self.manager, name="Barista")
        payload = push.call_args.args[1]["notification"]
        self.assertEqual(payload["title"], "Pozice vytvořena")

    def test_emails_go_out_in_the_recipients_language(self):
        self.client.force_login(self.manager)
        self.client.post(reverse("employee_delete", args=[self.employee.pk]))
        self.assertEqual(mail.outbox[0].subject, "Váš účet PlanShift byl smazán")

    def test_navigation_is_named_by_id_for_the_browser_to_translate(self):
        self.client.force_login(self.manager)
        nav = self.bootstrap(self.client.get(reverse("manager_shifts")))["nav"]
        self.assertEqual([link["id"] for link in nav], ["shifts", "search", "analytics", "team", "friends"])
