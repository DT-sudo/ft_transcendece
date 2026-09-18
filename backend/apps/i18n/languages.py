"""The languages PlanShift ships in (`settings.LANGUAGES`) and their writing direction."""

from __future__ import annotations

from django.conf import settings
from django.utils import translation


def is_supported(code: str | None) -> bool:
    return code in dict(settings.LANGUAGES)


def speaking(code: str | None):
    """Translate in `code` for the `with` block: an account's language, or the default when it has none yet.

    For what is written to someone other than the person making the request: their emails
    and live notifications.
    """
    return translation.override(code or settings.LANGUAGE_CODE)


def direction(code: str | None = None) -> str:
    """ "rtl" for Arabic, "ltr" for the others; the active language when no code is given."""
    return "rtl" if translation.get_language_info(code or translation.get_language())["bidi"] else "ltr"


def options() -> list[dict]:
    """The language switcher's choices, each named in its own language."""
    return [{"code": code, "name": name, "dir": direction(code)} for code, name in settings.LANGUAGES]
