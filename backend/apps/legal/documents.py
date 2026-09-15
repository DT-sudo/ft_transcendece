"""The Privacy Policy and Terms of Service, one translation per language.

Legal text is translated as whole documents (`content/en.py`, `cs.py`, `ar.py`) rather than
sentence by sentence through gettext: that is how such texts are translated and reviewed,
and each version stays readable on its own. Kept as data rather than templates so the same
structure renders through the React shell.
"""

from __future__ import annotations

from django.utils.translation import get_language

from .content import ar, cs, en

TRANSLATIONS = {"en": en, "cs": cs, "ar": ar}
NAMES = ("privacy", "terms")


def document(name: str) -> dict:
    """"privacy" or "terms", in the active language."""
    return TRANSLATIONS.get(get_language(), en).DOCUMENTS[name]
