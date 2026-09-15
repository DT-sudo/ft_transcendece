"""The languages PlanShift ships in (`settings.LANGUAGES`) and their writing direction."""

from __future__ import annotations

from django.conf import settings
from django.utils import translation


def is_supported(code: str | None) -> bool:
    return code in dict(settings.LANGUAGES)


def direction(code: str | None = None) -> str:
    """ "rtl" for Arabic, "ltr" for the others; the active language when no code is given."""
    return "rtl" if translation.get_language_info(code or translation.get_language())["bidi"] else "ltr"


def options() -> list[dict]:
    """The language switcher's choices, each named in its own language."""
    return [{"code": code, "name": name, "dir": direction(code)} for code, name in settings.LANGUAGES]
