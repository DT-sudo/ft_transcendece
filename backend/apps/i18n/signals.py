from __future__ import annotations

from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .languages import is_supported


@receiver(user_logged_in)
def keep_the_language_picked_before_signing_in(sender, request, user, **kwargs) -> None:
    """Switching language on the login page carries over into the account."""
    chosen = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME) if request is not None else None
    if is_supported(chosen):
        user.save_language(chosen)
