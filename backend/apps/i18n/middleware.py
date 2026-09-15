from __future__ import annotations

from django.conf import settings
from django.utils import translation

from .languages import is_supported


def set_language_cookie(response, code: str) -> None:
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        code,
        max_age=settings.LANGUAGE_COOKIE_AGE,
        secure=settings.LANGUAGE_COOKIE_SECURE,
        samesite=settings.LANGUAGE_COOKIE_SAMESITE,
    )


class UserLanguageMiddleware:
    """Signed-in users read PlanShift in the language saved on their account.

    Runs after Django's LocaleMiddleware, which picks the language for everyone else
    (the language cookie, else the browser's Accept-Language). An account without a
    saved language takes that detected one once, so the emails and live notifications
    it later receives are in a language its owner reads. The cookie follows the
    account, so the login page stays in the same language after signing out.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        signed_in = user.is_authenticated
        if signed_in:
            if not is_supported(user.language):
                user.language = request.LANGUAGE_CODE
                user.save(update_fields=["language"])
            translation.activate(user.language)
            request.LANGUAGE_CODE = user.language

        response = self.get_response(request)

        if signed_in and request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME) != user.language:
            set_language_cookie(response, user.language)
        return response
