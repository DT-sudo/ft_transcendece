"""Who can see whose profile, and the friend request flow."""

from __future__ import annotations

from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.accounts.models import User, UserRole
from apps.notifications.services import notify
from apps.realtime.events import push_to_user

from .models import Friendship, FriendshipStatus

# Tells the other side's open Friends and profile pages to re-read themselves.
FRIENDS_CHANGED = {"type": "friends.changed"}


class FriendshipError(Exception):
    """A friend request the flow refuses; the message is shown to the user."""


def between(a: User, b: User) -> Friendship | None:
    return Friendship.objects.filter(Q(from_user=a, to_user=b) | Q(from_user=b, to_user=a)).first()


def involving(user: User):
    return Friendship.objects.filter(Q(from_user=user) | Q(to_user=user))


def friend_ids(user_id: int) -> set[int]:
    rows = Friendship.objects.filter(
        Q(from_user_id=user_id) | Q(to_user_id=user_id), status=FriendshipStatus.ACCEPTED
    ).values_list("from_user_id", "to_user_id")
    return {sender if receiver == user_id else receiver for sender, receiver in rows}


def friends_of(user: User):
    return User.objects.filter(pk__in=friend_ids(user.pk), is_active=True).select_related("position").order_by("first_name", "last_name")


def colleagues_of(user: User):
    """Everyone but yourself and admins: the directory on the Colleagues page.

    Admins aren't colleagues - they don't get that page, so nobody could ever answer a
    request sent to one.
    """
    return (
        User.objects.filter(is_active=True)
        .exclude(pk=user.pk)
        .exclude(role=UserRole.ADMIN)
        .select_related("position")
        .order_by("first_name", "last_name")
    )


def can_view(viewer: User, person: User) -> bool:
    """Yourself, the accounts you manage, and anyone who isn't an admin - colleagues can
    always see each other's profile, friend status or not."""
    return viewer.pk == person.pk or viewer.manages(person) or not person.is_admin


def friendship_relation(friendship: Friendship, viewer: User) -> dict:
    """`{"state", "friendshipId"}`: "friends", or who waits on whom ("outgoing" when `viewer` asked, else "incoming")."""
    if friendship.accepted:
        state = "friends"
    else:
        state = "outgoing" if friendship.from_user_id == viewer.pk else "incoming"
    return {"state": state, "friendshipId": friendship.id}


def relation(viewer: User, person: User) -> dict:
    """What the friend button on `person`'s profile offers `viewer`."""
    if viewer.pk == person.pk:
        return {"state": "self"}
    friendship = between(viewer, person)
    return {"state": "none"} if friendship is None else friendship_relation(friendship, viewer)


def card(user: User) -> dict:
    """Name, picture and role line: what every list of people shows."""
    return {
        "id": user.id,
        "fullName": user.display_name,
        "avatarUrl": user.avatar_url,
        "role": user.role_label,
        "profileUrl": reverse("profile", args=[user.id]),
    }


def friend_urls() -> dict:
    return {
        "request": reverse("friend_request"),
        "accept": reverse("friend_accept", args=[0]),
        "end": reverse("friend_end", args=[0]),
    }


def send_request(sender: User, receiver: User) -> Friendship:
    if receiver.pk == sender.pk:
        raise FriendshipError(_("You can't add yourself as a friend."))
    existing = between(sender, receiver)
    if existing is None:
        friendship = Friendship.objects.create(from_user=sender, to_user=receiver)
        notify([receiver], "friend.requested", actor=sender, name=sender.display_name)
        push_to_user(receiver.pk, FRIENDS_CHANGED)
        return friendship
    if existing.accepted:
        raise FriendshipError(_("You and %(name)s are already friends.") % {"name": receiver.display_name})
    if existing.from_user_id == sender.pk:
        raise FriendshipError(_("You already sent %(name)s a friend request.") % {"name": receiver.display_name})
    # They asked first, so asking back is a yes.
    accept(existing)
    return existing


def accept(friendship: Friendship) -> None:
    friendship.status = FriendshipStatus.ACCEPTED
    friendship.accepted_at = timezone.now()
    friendship.save(update_fields=["status", "accepted_at"])
    notify([friendship.from_user], "friend.accepted", actor=friendship.to_user, name=friendship.to_user.display_name)
    push_to_user(friendship.from_user_id, FRIENDS_CHANGED)


def end(friendship: Friendship, user: User) -> str:
    """Decline, cancel or unfriend (they all delete the row); returns the flash message for `user`."""
    other = friendship.other(user)
    if friendship.accepted:
        notify([other], "friend.removed", actor=user, name=user.display_name)
        text = _("Removed %(name)s from your friends.") % {"name": other.display_name}
    elif friendship.to_user_id == user.pk:
        text = _("Declined %(name)s's friend request.") % {"name": other.display_name}
    else:
        text = _("Cancelled your friend request to %(name)s.") % {"name": other.display_name}
    friendship.delete()
    push_to_user(other.pk, FRIENDS_CHANGED)
    return text
