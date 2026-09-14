"""Profiles, account settings, profile pictures and friends (the "Major: Standard user management" module)."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.accounts.models import User
from apps.shell import field_errors, flash_redirect, render_app

from . import avatars, presence, services
from .forms import AvatarForm, ProfileForm
from .models import Friendship, FriendshipStatus


def _visible_person_or_404(request: HttpRequest, user_id: int) -> User:
    person = get_object_or_404(User.objects.select_related("position"), pk=user_id, is_active=True)
    if not services.can_view(request.user, person):
        raise Http404
    return person


# ── Profile page ────────────────────────────────────────────────────────────


@login_required
@require_GET
def profile(request: HttpRequest, user_id: int) -> HttpResponse:
    person = _visible_person_or_404(request, user_id)
    relation = services.relation(request.user, person)
    # Friends (and you) see the email, online status and friend list; a manager sees the email too.
    close = relation["state"] in ("self", "friends")
    friends = services.friends_of(person)

    return render_app(
        request,
        page="profile",
        title=person.display_name,
        data={
            "person": {
                **services.card(person),
                "bio": person.bio,
                "memberSince": person.date_joined.date().isoformat(),
                "email": person.email if close or request.user.manages(person) else None,
                "status": presence.status(person) if close else None,
                "friendCount": len(friends),
            },
            "relation": relation,
            "friends": [services.card(friend) for friend in friends] if close else None,
            "urls": services.friend_urls(),
        },
    )


@login_required
@require_GET
def avatar(request: HttpRequest, user_id: int) -> FileResponse:
    """A profile picture, for those who may see the profile. Its URL changes with each upload, hence the long cache."""
    person = _visible_person_or_404(request, user_id)
    if not person.avatar:
        raise Http404
    response = FileResponse(person.avatar.open("rb"), content_type="image/webp")
    response["Cache-Control"] = "private, max-age=31536000, immutable"
    return response


# ── Account settings ────────────────────────────────────────────────────────


@login_required
@require_http_methods(["GET", "POST"])
def account_settings(request: HttpRequest) -> HttpResponse:
    """Your own profile, picture and password. Each card posts its `section`; errors re-render in place."""
    user = request.user
    section = request.POST.get("section") if request.method == "POST" else None

    profile_form = ProfileForm(request.POST if section == "profile" else None, instance=user)
    password_form = PasswordChangeForm(user, request.POST if section == "password" else None)
    avatar_form = AvatarForm(request.POST if section == "avatar" else None, request.FILES if section == "avatar" else None)

    if section == "profile" and profile_form.is_valid():
        profile_form.save()
        return flash_redirect(request, messages.SUCCESS, "Profile updated.", "account_settings")
    if section == "password" and password_form.is_valid():
        password_form.save()
        update_session_auth_hash(request, password_form.user)  # stay signed in with the new password
        return flash_redirect(request, messages.SUCCESS, "Password changed.", "account_settings")
    if section == "avatar" and avatar_form.is_valid():
        avatars.replace_avatar(user, avatars.to_webp(avatar_form.cleaned_data["avatar"]))
        return flash_redirect(request, messages.SUCCESS, "Profile picture updated.", "account_settings")
    if section == "remove_avatar":
        avatars.replace_avatar(user, None)
        return flash_redirect(request, messages.SUCCESS, "Profile picture removed.", "account_settings")

    posted_profile = section == "profile"
    return render_app(
        request,
        page="account-settings",
        title="Account settings",
        data={
            "values": {
                "fullName": request.POST.get("full_name", "") if posted_profile else user.get_full_name(),
                "email": request.POST.get("email", "") if posted_profile else user.email,
                "bio": request.POST.get("bio", "") if posted_profile else user.bio,
            },
            "errors": {
                "profile": field_errors(profile_form) if posted_profile else {},
                "password": field_errors(password_form) if section == "password" else {},
                "avatar": field_errors(avatar_form).get("avatar", "") if section == "avatar" else "",
            },
            "person": services.card(user),
            "avatar": {"maxBytes": avatars.MAX_BYTES, "accept": ",".join(avatars.FORMATS.values())},
        },
    )


# ── Friends ─────────────────────────────────────────────────────────────────


@login_required
@require_GET
def friends(request: HttpRequest) -> HttpResponse:
    """Everyone the user has a friendship with, sorted by its state: friends, requests to answer, requests sent."""
    user = request.user
    lists = {"friends": [], "incoming": [], "outgoing": []}
    rows = services.involving(user).select_related("from_user__position", "to_user__position").order_by("-created_at")
    for friendship in rows:
        other = friendship.other(user)
        if not other.is_active:
            continue
        relation = services.friendship_relation(friendship, user)
        extra = {"status": presence.status(other)} if friendship.accepted else {"sentAt": friendship.created_at.isoformat()}
        lists[relation["state"]].append({**services.card(other), "relation": relation, **extra})
    lists["friends"].sort(key=lambda friend: (not friend["status"]["online"], friend["fullName"].lower()))

    return render_app(
        request,
        page="friends",
        title="Friends",
        nav_active="friends",
        data={**lists, "urls": services.friend_urls()},
    )


def _back(request: HttpRequest, level: int, text: str) -> HttpResponse:
    """Back to the page the action came from (a profile or the Friends page)."""
    target = request.POST.get("next", "")
    if not url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        target = "friends"
    return flash_redirect(request, level, text, target)


@login_required
@require_POST
def friend_request(request: HttpRequest) -> HttpResponse:
    """Ask by email (the Friends page) or by id (the button on a profile you can already see)."""
    user_id = request.POST.get("user_id", "")
    if user_id:
        receiver = User.objects.filter(pk=user_id, is_active=True).first() if user_id.isdigit() else None
        if receiver is None or not services.can_view(request.user, receiver):
            return _back(request, messages.ERROR, "That person was not found.")
    else:
        email = (request.POST.get("email") or "").strip().lower()
        receiver = User.objects.filter(username=email, is_active=True).first() if email else None
        if receiver is None:
            return _back(request, messages.ERROR, "No account uses that email address.")

    try:
        friendship = services.send_request(request.user, receiver)
    except services.FriendshipError as error:
        return _back(request, messages.ERROR, str(error))
    if friendship.accepted:
        return _back(request, messages.SUCCESS, f"You and {receiver.display_name} are now friends.")
    return _back(request, messages.SUCCESS, f"Friend request sent to {receiver.display_name}.")


@login_required
@require_POST
def friend_accept(request: HttpRequest, friendship_id: int) -> HttpResponse:
    friendship = get_object_or_404(
        Friendship.objects.select_related("from_user", "to_user"),
        pk=friendship_id,
        to_user=request.user,
        status=FriendshipStatus.PENDING,
    )
    services.accept(friendship)
    return _back(request, messages.SUCCESS, f"You and {friendship.from_user.display_name} are now friends.")


@login_required
@require_POST
def friend_end(request: HttpRequest, friendship_id: int) -> HttpResponse:
    """Decline an incoming request, cancel your own, or unfriend."""
    friendship = get_object_or_404(services.involving(request.user).select_related("from_user", "to_user"), pk=friendship_id)
    return _back(request, messages.SUCCESS, services.end(friendship, request.user))
