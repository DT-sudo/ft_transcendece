"""Profiles, account settings and profile pictures (the "Major: Standard user management" module)."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_http_methods

from apps.accounts.models import User
from apps.shell import field_errors, flash_redirect, render_app

from . import avatars, services
from .forms import AvatarForm, ProfileForm


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

    return render_app(
        request,
        page="profile",
        title=person.display_name,
        data={
            "person": {
                **services.card(person),
                "bio": person.bio,
                "memberSince": person.date_joined.date().isoformat(),
                "email": person.email,
            },
            "relation": {"state": "self" if person.pk == request.user.pk else "none"},
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

