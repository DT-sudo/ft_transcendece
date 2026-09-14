"""Who can see whose profile."""

from __future__ import annotations

from django.urls import reverse

from apps.accounts.models import User


def can_view(viewer: User, person: User) -> bool:
    """Yourself, and the accounts you manage."""
    return viewer.pk == person.pk or viewer.manages(person)


def card(user: User) -> dict:
    """Name, picture and role line: what every list of people shows."""
    return {
        "id": user.id,
        "fullName": user.display_name,
        "avatarUrl": user.avatar_url,
        "role": user.role_label,
        "profileUrl": reverse("profile", args=[user.id]),
    }
