"""The page shell: every view renders the React bundle plus one JSON payload.

Also holds the two ways a view answers a form POST: a flash message + redirect
(shown as a toast) or, for the auth pages, field errors re-rendered in place.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.messages import get_messages
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest, HttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import redirect, render
from django.templatetags.static import static
from django.urls import reverse

VITE_ENTRY = "src/main.jsx"


def flash_redirect(request: HttpRequest, level: int, text: str, to: str) -> HttpResponse:
    """Add a flash message and redirect; the message arrives as a toast."""
    messages.add_message(request, level, text)
    return redirect(to)


def first_form_error(form, default: str) -> str:
    """First error message on a form, for flows that redirect instead of re-rendering."""
    return next((errors[0] for errors in form.errors.values() if errors), default)


def field_errors(form) -> dict[str, str]:
    """Flatten a form's field errors into {field: first message} for React."""
    return {name: errors[0] for name, errors in form.errors.items() if errors}


@lru_cache(maxsize=1)
def _vite_manifest() -> dict:
    path = settings.FRONTEND_DIST_DIR / ".vite" / "manifest.json"
    if not path.exists():
        raise ImproperlyConfigured(f"Vite manifest not found at {path}. Run `npm install && npm run build` in frontend/.")
    return json.loads(path.read_text())


def _bundle() -> dict[str, Any]:
    """Static URLs of the built bundle's stylesheet(s) and script."""
    if settings.DEBUG:
        _vite_manifest.cache_clear()  # rebuilds are frequent in development
    chunk = _vite_manifest()[VITE_ENTRY]
    return {"css": [static(css) for css in chunk.get("css", [])], "js": static(chunk["file"])}


def _nav_links(user, active: str) -> list[dict[str, Any]]:
    if not user.is_authenticated:
        return []
    if user.is_manager:
        items = [
            ("manager_shifts", "Shifts"),
            ("manager_shift_search", "Search"),
            ("manager_analytics", "Analytics"),
            ("manager_employees", "Users" if user.is_admin else "Team"),
        ]
    else:
        items = [("employee_shifts", "My Shifts")]
    return [{"href": reverse(name), "label": label, "active": name == active} for name, label in items]


def _user_context(user) -> dict[str, Any] | None:
    if not user.is_authenticated:
        return None
    return {
        "id": user.id,  # keys the browser's notification history per account
        "displayName": user.display_name,
        "role": "Manager" if user.is_manager else (user.position.name if user.position else "Employee"),
    }


def render_app(request: HttpRequest, *, page: str, title: str, data: dict[str, Any] | None = None, nav_active: str = "") -> HttpResponse:
    bootstrap = {
        "page": page,
        "csrfToken": get_token(request),
        "user": _user_context(request.user),
        "nav": _nav_links(request.user, nav_active),
        # Present on every page so the footer can link the Privacy Policy and
        # Terms of Service from anywhere, signed in or not.
        "urls": {
            "logout": reverse("logout"),
            "privacy": reverse("privacy_policy"),
            "terms": reverse("terms_of_service"),
            "privacyCenter": reverse("privacy_center"),
        },
        "messages": [{"level": message.level_tag, "text": message.message} for message in get_messages(request)],
        "data": data or {},
    }
    return render(request, "app.html", {"title": title, "bundle": _bundle(), "bootstrap": bootstrap})
