from __future__ import annotations

import shutil
import tempfile
from io import BytesIO
from pathlib import Path
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from apps.accounts.models import User, UserRole
from apps.scheduling.models import Position

PASSWORD = "pw-for-tests-42"


def picture(name="me.png", fmt="PNG", size=(600, 400), exif=None) -> SimpleUploadedFile:
    buffer = BytesIO()
    Image.new("RGB", size, (200, 30, 30)).save(buffer, fmt, **({"exif": exif} if exif else {}))
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=f"image/{fmt.lower()}")


class ProfilesTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.barista = Position.objects.create(name="Barista")

        def make(name, role=UserRole.EMPLOYEE):
            return User.objects.create_user(
                username=f"{name}@example.com",
                email=f"{name}@example.com",
                password=PASSWORD,
                role=role,
                first_name=name.title(),
                last_name="Test",
                position=cls.barista if role == UserRole.EMPLOYEE else None,
            )

        cls.alice, cls.bob, cls.carol = make("alice"), make("bob"), make("carol")
        cls.manager = make("maya", UserRole.MANAGER)

    def profile_data(self, viewer, person):
        self.client.force_login(viewer)
        return self.client.get(reverse("profile", args=[person.id]), {"format": "json"})


class ProfilePageTests(ProfilesTestCase):
    def test_your_own_profile_shows_everything(self):
        data = self.profile_data(self.alice, self.alice).json()

        self.assertEqual(data["relation"], {"state": "self"})
        self.assertEqual(data["person"]["email"], "alice@example.com")
        self.assertEqual(data["person"]["role"], "Barista")

    def test_strangers_get_404(self):
        self.assertEqual(self.profile_data(self.alice, self.bob).status_code, 404)

    def test_managers_see_their_employees_but_not_the_other_way_round(self):
        data = self.profile_data(self.manager, self.alice).json()
        self.assertEqual(data["person"]["email"], "alice@example.com")

        self.assertEqual(self.profile_data(self.alice, self.manager).status_code, 404)

    def test_a_deactivated_account_has_no_profile(self):
        User.objects.filter(pk=self.alice.pk).update(is_active=False)
        self.assertEqual(self.profile_data(self.manager, self.alice).status_code, 404)

    def test_header_links_the_profile(self):
        self.client.force_login(self.alice)
        user = self.client.get(reverse("account_settings")).context["bootstrap"]["user"]
        self.assertEqual(user["profileUrl"], reverse("profile", args=[self.alice.id]))
        self.assertIsNone(user["avatarUrl"])


class AccountSettingsTests(ProfilesTestCase):
    def setUp(self) -> None:
        self.client.force_login(self.alice)

    def post(self, section, **fields):
        return self.client.post(reverse("account_settings"), {"section": section, **fields})

    def profile(self, **overrides):
        return self.post("profile", **{"full_name": "Alice Test", "email": "alice@example.com", "bio": "", **overrides})

    def test_update_name_and_bio(self):
        response = self.profile(full_name="Alice  Cooper", bio="Morning shifts, strong coffee.")

        self.assertRedirects(response, reverse("account_settings"))
        self.alice.refresh_from_db()
        self.assertEqual((self.alice.first_name, self.alice.last_name), ("Alice", "Cooper"))
        self.assertEqual(self.alice.bio, "Morning shifts, strong coffee.")

    def test_changing_the_email_takes_the_current_password(self):
        response = self.profile(email="new@example.com")

        errors = response.context["bootstrap"]["data"]["errors"]["profile"]
        self.assertIn("current_password", errors)
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.email, "alice@example.com")

        self.profile(email="New@Example.com", current_password=PASSWORD)
        self.alice.refresh_from_db()
        # The email is the login, so the username follows it.
        self.assertEqual((self.alice.email, self.alice.username), ("new@example.com", "new@example.com"))

    def test_the_email_must_stay_unique(self):
        response = self.profile(email="bob@example.com", current_password=PASSWORD)
        self.assertIn("email", response.context["bootstrap"]["data"]["errors"]["profile"])

    def test_a_refused_edit_does_not_reach_the_header(self):
        response = self.profile(full_name="Mallory Evil", email="bob@example.com", current_password=PASSWORD)

        self.assertEqual(response.context["bootstrap"]["user"]["fullName"], "Alice Test")
        self.assertEqual(response.context["bootstrap"]["data"]["values"]["fullName"], "Mallory Evil")

    def test_change_password_and_stay_signed_in(self):
        response = self.post("password", old_password=PASSWORD, new_password1="brand-new-pass-7", new_password2="brand-new-pass-7")

        self.assertRedirects(response, reverse("account_settings"))
        self.alice.refresh_from_db()
        self.assertTrue(self.alice.check_password("brand-new-pass-7"))
        self.assertEqual(self.client.get(reverse("account_settings")).status_code, 200)

    def test_a_wrong_current_password_is_refused(self):
        response = self.post("password", old_password="nope", new_password1="brand-new-pass-7", new_password2="brand-new-pass-7")

        self.assertIn("old_password", response.context["bootstrap"]["data"]["errors"]["password"])
        self.alice.refresh_from_db()
        self.assertTrue(self.alice.check_password(PASSWORD))

    def test_settings_need_a_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("account_settings")).status_code, 302)


class AvatarTests(ProfilesTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.media = tempfile.mkdtemp()
        cls.enterClassContext(override_settings(MEDIA_ROOT=cls.media))

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(cls.media, ignore_errors=True)

    def upload(self, user, file):
        self.client.force_login(user)
        response = self.client.post(reverse("account_settings"), {"section": "avatar", "avatar": file})
        user.refresh_from_db()
        return response

    def stored(self, user) -> Path:
        return Path(self.media) / user.avatar.name

    def test_an_upload_is_stored_as_a_small_webp(self):
        response = self.upload(self.alice, picture(size=(900, 500)))

        self.assertRedirects(response, reverse("account_settings"))
        self.assertRegex(self.alice.avatar.name, r"^avatars/[0-9a-f]{32}\.webp$")
        with Image.open(self.stored(self.alice)) as image:
            self.assertEqual((image.format, image.size), ("WEBP", (256, 256)))
        header = self.client.get(reverse("account_settings")).context["bootstrap"]["user"]
        self.assertTrue(header["avatarUrl"].startswith(reverse("avatar", args=[self.alice.id])))

    def test_camera_and_location_metadata_are_dropped(self):
        exif = Image.Exif()
        exif[0x010F] = "SpyCam"  # camera maker
        self.upload(self.alice, picture("me.jpg", "JPEG", exif=exif))

        with Image.open(self.stored(self.alice)) as image:
            self.assertEqual(dict(image.getexif()), {})

    def test_a_file_that_is_not_a_picture_is_refused(self):
        response = self.upload(self.alice, SimpleUploadedFile("evil.png", b"<?php system($_GET[1]); ?>", content_type="image/png"))

        self.assertTrue(response.context["bootstrap"]["data"]["errors"]["avatar"])
        self.assertFalse(self.alice.avatar)

    def test_a_picture_over_the_size_limit_is_refused(self):
        with mock.patch("apps.profiles.avatars.MAX_BYTES", 100):
            response = self.upload(self.alice, picture())

        self.assertIn("MB or smaller", response.context["bootstrap"]["data"]["errors"]["avatar"])
        self.assertFalse(self.alice.avatar)

    def test_replacing_or_removing_deletes_the_old_file(self):
        self.upload(self.alice, picture())
        first = self.stored(self.alice)
        self.upload(self.alice, picture("second.png"))
        second = self.stored(self.alice)
        self.assertFalse(first.exists())
        self.assertTrue(second.exists())

        self.client.post(reverse("account_settings"), {"section": "remove_avatar"})
        self.alice.refresh_from_db()
        self.assertFalse(self.alice.avatar)
        self.assertFalse(second.exists())

    def test_deleting_the_account_deletes_the_picture(self):
        self.upload(self.alice, picture())
        path = self.stored(self.alice)

        self.alice.delete()

        self.assertFalse(path.exists())

    def test_a_picture_is_served_only_to_those_who_may_see_the_profile(self):
        self.upload(self.alice, picture())
        url = reverse("avatar", args=[self.alice.id])

        response = self.client.get(url)
        self.assertEqual((response.status_code, response["Content-Type"]), (200, "image/webp"))

        self.client.force_login(self.bob)
        self.assertEqual(self.client.get(url).status_code, 404)

