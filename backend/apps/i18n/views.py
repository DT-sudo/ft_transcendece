"""The language switcher (the "Minor: multiple languages" and "Minor: RTL" modules)."""

from __future__ import annotations

from django.http import HttpRequest, JsonResponse
from django.utils import translation
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.profiles.services import card

from .languages import direction, is_supported
from .middleware import set_language_cookie


@require_POST
def set_language(request: HttpRequest) -> JsonResponse:
    """Save the choice (on the account when signed in, in a cookie always).

    Answers with what the page needs to switch in place without a reload: the
    direction, and the header's user card, whose role line is translated on the server.
    """
    code = request.POST.get("language", "")
    if not is_supported(code):
        return JsonResponse({"error": _("That language is not available.")}, status=400)

    user = request.user
    if user.is_authenticated and user.language != code:
        user.language = code
        user.save(update_fields=["language"])

    translation.activate(code)
    response = JsonResponse(
        {"language": code, "dir": direction(code), "user": card(user) if user.is_authenticated else None}
    )
    set_language_cookie(response, code)
    return response
