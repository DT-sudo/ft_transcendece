from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.http import HttpRequest


class EmailBackend(ModelBackend):
    """Authenticate with an email address instead of a username.

    Emails are stored lowercase and are unique, but `filter().first()` is used
    rather than `get()` so historical duplicates cannot raise. The password
    hasher runs even when no user matches, which keeps the response time the
    same for known and unknown addresses (no timing oracle on registrations).
    """

    def authenticate(
        self,
        request: HttpRequest | None,
        username: str | None = None,
        password: str | None = None,
        **kwargs,
    ):
        User = get_user_model()
        email = (kwargs.get("email") or username or "").strip().lower()
        if not email or not password:
            return None

        user = User.objects.filter(email__iexact=email).order_by("pk").first()
        if user is None:
            User().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
