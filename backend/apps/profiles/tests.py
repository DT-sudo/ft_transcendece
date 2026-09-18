from __future__ import annotations

import asyncio
import json
import shutil
import tempfile
from datetime import timedelta
from io import BytesIO
from pathlib import Path
from unittest import mock

from asgiref.sync import async_to_sync, sync_to_async
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from apps.accounts.models import Position, User, UserRole
from apps.notifications.models import Notification
from apps.realtime.events import user_group
from apps.realtime.tests import IN_MEMORY_LAYER, _as_user, next_event

from . import presence
from .models import Friendship, FriendshipStatus

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
        cls.admin = make("adam", UserRole.ADMIN)

    def befriend(self, sender, receiver, accepted=True) -> Friendship:
        status = FriendshipStatus.ACCEPTED if accepted else FriendshipStatus.PENDING
        return Friendship.objects.create(from_user=sender, to_user=receiver, status=status)

    def profile_data(self, viewer, person):
        self.client.force_login(viewer)
        return self.client.get(reverse("profile", args=[person.id]), {"format": "json"})


class ProfilePageTests(ProfilesTestCase):
    def test_your_own_profile_shows_everything(self):
        data = self.profile_data(self.alice, self.alice).json()

        self.assertEqual(data["relation"], {"state": "self"})
        self.assertEqual(data["person"]["email"], "alice@example.com")
        self.assertEqual(data["person"]["role"], "Barista")
        self.assertIsNotNone(data["person"]["status"])

    def test_strangers_can_view_the_profile_without_private_details(self):
        response = self.profile_data(self.alice, self.bob)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["relation"], {"state": "none"})
        self.assertIsNone(data["person"]["email"])
        self.assertIsNone(data["person"]["status"])
        self.assertIsNone(data["friends"])

    def test_admins_are_not_visible_to_colleagues(self):
        self.assertEqual(self.profile_data(self.alice, self.admin).status_code, 404)
        self.assertEqual(self.profile_data(self.manager, self.admin).status_code, 404)

    def test_friends_see_email_status_and_friend_list(self):
        self.befriend(self.alice, self.bob)

        data = self.profile_data(self.alice, self.bob).json()

        self.assertEqual(data["relation"]["state"], "friends")
        self.assertEqual(data["person"]["email"], "bob@example.com")
        self.assertEqual(data["person"]["status"], {"online": False, "lastSeen": None})
        self.assertEqual([friend["id"] for friend in data["friends"]], [self.alice.id])

    def test_a_pending_request_shows_the_profile_without_private_details(self):
        self.befriend(self.bob, self.alice, accepted=False)

        data = self.profile_data(self.alice, self.bob).json()

        self.assertEqual(data["relation"]["state"], "incoming")
        self.assertIsNone(data["person"]["email"])
        self.assertIsNone(data["person"]["status"])
        self.assertIsNone(data["friends"])

    def test_colleagues_see_each_other_without_private_details_either_way(self):
        """A manager isn't privileged here: email and online status are for friends (and the admin)."""
        for viewer, person in ((self.manager, self.alice), (self.alice, self.manager)):
            with self.subTest(viewer=viewer.first_name):
                response = self.profile_data(viewer, person)
                self.assertEqual(response.status_code, 200)
                self.assertIsNone(response.json()["person"]["email"])
                self.assertIsNone(response.json()["person"]["status"])

    def test_the_admin_sees_the_email_of_every_account_they_manage(self):
        data = self.profile_data(self.admin, self.alice).json()

        self.assertEqual(data["person"]["email"], "alice@example.com")
        self.assertIsNone(data["person"]["status"])  # online status is still friends only

    def test_a_deactivated_account_has_no_profile(self):
        User.objects.filter(pk=self.alice.pk).update(is_active=False)
        self.assertEqual(self.profile_data(self.manager, self.alice).status_code, 404)

    def test_header_links_the_profile(self):
        self.client.force_login(self.alice)
        user = self.client.get(reverse("friends")).context["bootstrap"]["user"]
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
        header = self.client.get(reverse("friends")).context["bootstrap"]["user"]
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

        # Any colleague can see it, friends or not.
        self.client.force_login(self.bob)
        self.assertEqual(self.client.get(url).status_code, 200)

        # An admin isn't a colleague, so their own picture stays private.
        self.upload(self.admin, picture())
        admin_url = reverse("avatar", args=[self.admin.id])
        self.client.force_login(self.bob)
        self.assertEqual(self.client.get(admin_url).status_code, 404)


class FriendshipTests(ProfilesTestCase):
    def ask(self, sender, **fields):
        self.client.force_login(sender)
        return self.client.post(reverse("friend_request"), fields)

    def flash(self, response) -> str:
        return [str(message) for message in response.wsgi_request._messages][-1]

    def test_a_request_by_id_notifies_the_other_person(self):
        response = self.ask(self.alice, user_id=self.bob.id)

        self.assertRedirects(response, reverse("friends"))
        friendship = Friendship.objects.get()
        self.assertEqual((friendship.from_user, friendship.to_user, friendship.status), (self.alice, self.bob, "pending"))
        self.assertEqual(Notification.objects.get(recipient=self.bob).title, "New friend request")

    def test_refused_requests(self):
        cases = {
            "999999": "That person was not found.",
            str(self.alice.id): "You can't add yourself as a friend.",
        }
        for user_id, message in cases.items():
            with self.subTest(user_id=user_id):
                self.assertEqual(self.flash(self.ask(self.alice, user_id=user_id)), message)
        self.assertFalse(Friendship.objects.exists())

        self.ask(self.alice, user_id=self.bob.id)
        self.assertEqual(self.flash(self.ask(self.alice, user_id=self.bob.id)), "You already sent Bob Test a friend request.")
        self.assertEqual(Friendship.objects.count(), 1)

    def test_a_request_needs_a_real_colleague(self):
        """An admin isn't a colleague, so asking one is refused like asking a nonexistent id."""
        response = self.ask(self.carol, user_id=self.admin.id)
        self.assertEqual(self.flash(response), "That person was not found.")
        self.assertFalse(Friendship.objects.exists())

    def test_asking_back_accepts(self):
        self.befriend(self.bob, self.alice, accepted=False)

        self.ask(self.alice, user_id=self.bob.id)

        self.assertTrue(Friendship.objects.get().accepted)

    def test_admins_have_no_colleagues_feature(self):
        self.client.force_login(self.admin)
        self.assertRedirects(self.client.get(reverse("friends")), reverse("manager_employees"))
        self.assertRedirects(self.ask(self.admin, user_id=self.alice.id), reverse("manager_employees"))
        self.assertFalse(Friendship.objects.exists())

    def test_only_the_receiver_can_accept(self):
        friendship = self.befriend(self.alice, self.bob, accepted=False)
        url = reverse("friend_accept", args=[friendship.id])

        self.client.force_login(self.alice)
        self.assertEqual(self.client.post(url).status_code, 404)

        self.client.force_login(self.bob)
        self.client.post(url)
        friendship.refresh_from_db()
        self.assertTrue(friendship.accepted)
        self.assertEqual(Notification.objects.get(recipient=self.alice).title, "Friend request accepted")

    def test_declining_cancelling_and_unfriending_delete_the_row(self):
        for user, accepted in ((self.bob, False), (self.alice, False), (self.alice, True)):
            with self.subTest(user=user.first_name, accepted=accepted):
                friendship = self.befriend(self.alice, self.bob, accepted=accepted)
                self.client.force_login(self.carol)
                self.assertEqual(self.client.post(reverse("friend_end", args=[friendship.id])).status_code, 404)

                self.client.force_login(user)
                self.client.post(reverse("friend_end", args=[friendship.id]))
                self.assertFalse(Friendship.objects.exists())

    def test_a_pair_has_one_row_whichever_way_round(self):
        self.befriend(self.alice, self.bob, accepted=False)
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.befriend(self.bob, self.alice, accepted=False)

    def test_redirects_stay_on_this_site(self):
        response = self.ask(self.alice, user_id=self.bob.id, next="https://evil.example/")
        self.assertRedirects(response, reverse("friends"))

    def test_the_friends_page_sorts_people_into_lists(self):
        self.befriend(self.alice, self.bob)
        self.befriend(self.carol, self.alice, accepted=False)
        self.befriend(self.alice, self.manager, accepted=False)
        self.client.force_login(self.alice)

        data = self.client.get(reverse("friends"), {"format": "json"}).json()

        self.assertEqual([friend["id"] for friend in data["friends"]], [self.bob.id])
        self.assertEqual([request["id"] for request in data["incoming"]], [self.carol.id])
        self.assertEqual([request["id"] for request in data["outgoing"]], [self.manager.id])
        # Each of them is shown once, in the section that can act on them.
        self.assertEqual(data["colleagues"], [])

    def test_the_directory_lists_every_colleague_but_yourself_and_admins(self):
        self.client.force_login(self.alice)

        data = self.client.get(reverse("friends"), {"format": "json"}).json()

        self.assertEqual({person["id"] for person in data["colleagues"]}, {self.bob.id, self.carol.id, self.manager.id})

    def test_asking_someone_takes_them_out_of_the_directory(self):
        self.ask(self.alice, user_id=self.bob.id)
        self.client.force_login(self.alice)

        data = self.client.get(reverse("friends"), {"format": "json"}).json()

        self.assertNotIn(self.bob.id, {person["id"] for person in data["colleagues"]})
        self.assertEqual([request["id"] for request in data["outgoing"]], [self.bob.id])

    @override_settings(CHANNEL_LAYERS=IN_MEMORY_LAYER)
    def test_the_other_side_hears_about_it_live(self):
        layer = get_channel_layer()
        channel = async_to_sync(layer.new_channel)()
        async_to_sync(layer.group_add)(user_group(self.bob.id), channel)

        with self.captureOnCommitCallbacks(execute=True):
            self.ask(self.alice, user_id=self.bob.id)

        self.assertEqual(next_event(layer, channel)["type"], "notification")
        self.assertEqual(next_event(layer, channel), {"type": "friends.changed"})

    def test_the_data_export_lists_friends(self):
        self.befriend(self.alice, self.bob)
        self.client.force_login(self.alice)

        export = json.loads(self.client.get(reverse("privacy_export_data")).content)

        self.assertEqual(
            [(friend["name"], friend["status"], friend["requested_by"]) for friend in export["friends"]],
            [("Bob Test", "accepted", "you")],
        )


class PresenceTests(ProfilesTestCase):
    def test_online_while_any_page_is_open(self):
        self.assertTrue(presence.socket_opened(self.alice.id))
        self.assertFalse(presence.socket_opened(self.alice.id))  # a second tab changes nothing

        self.assertFalse(presence.socket_closed(self.alice.id))
        self.assertTrue(presence.socket_closed(self.alice.id))
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.open_sockets, 0)
        self.assertIsNotNone(self.alice.last_seen)

    def test_a_stale_count_starts_over(self):
        # Three sockets a stopped server never closed, last confirmed ten minutes ago.
        User.objects.filter(pk=self.alice.pk).update(open_sockets=3, last_seen=timezone.now() - timedelta(minutes=10))
        self.alice.refresh_from_db()
        self.assertFalse(presence.is_online(self.alice))

        self.assertTrue(presence.socket_opened(self.alice.id))
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.open_sockets, 1)


@override_settings(CHANNEL_LAYERS=IN_MEMORY_LAYER)
class LivePresenceTests(ProfilesTestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        Friendship.objects.create(from_user=cls.alice, to_user=cls.bob, status=FriendshipStatus.ACCEPTED)

    async def listen(self, user):
        layer = get_channel_layer()
        channel = await layer.new_channel()
        await layer.group_add(user_group(user.id), channel)
        return lambda timeout=1: asyncio.wait_for(layer.receive(channel), timeout)

    async def test_friends_hear_when_you_come_online_and_leave(self):
        bob_hears, carol_hears = await self.listen(self.bob), await self.listen(self.carol)

        communicator = WebsocketCommunicator(_as_user(self.alice), "/ws/schedule/")
        await communicator.connect()
        event = (await bob_hears())["event"]
        self.assertEqual((event["type"], event["userId"], event["status"]["online"]), ("friend.status", self.alice.id, True))

        await communicator.disconnect()
        self.assertFalse((await bob_hears())["event"]["status"]["online"])

        with self.assertRaises(asyncio.TimeoutError):
            await carol_hears(timeout=0.2)  # not a friend
        alice = await sync_to_async(User.objects.get)(pk=self.alice.pk)
        self.assertEqual(alice.open_sockets, 0)
