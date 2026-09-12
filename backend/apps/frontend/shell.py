"""Shared page shell: every view renders one React entry plus a JSON payload."""

from __future__ import annotations

from typing import Any

from django.contrib.messages import get_messages
from django.http import HttpRequest, HttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.urls import reverse

APP_TEMPLATE = "app.html"


def _nav_links(user, active: str) -> list[dict[str, Any]]:
    if not getattr(user, "is_authenticated", False):
        return []

    if user.is_manager:
        items = [("manager_shifts", "Shifts"), ("manager_employees", "Team")]
    else:
        items = [("employee_shifts", "My Shifts")]

    return [
        {"href": reverse(name), "label": label, "active": name == active}
        for name, label in items
    ]


def _user_context(user) -> dict[str, Any] | None:
    if not getattr(user, "is_authenticated", False):
        return None

    display_name = user.get_full_name() or user.username
    initials = "".join(part[0] for part in display_name.split()[:2] if part) or display_name[:1]
    position = getattr(getattr(user, "position", None), "name", None)

    return {
        "id": user.id,
        "displayName": display_name,
        "initials": initials.upper(),
        "role": "Manager" if user.is_manager else (position or "Employee"),
        "isManager": bool(user.is_manager),
    }


def render_app(
    request: HttpRequest,
    *,
    entry: str,
    title: str,
    data: dict[str, Any] | None = None,
    description: str = "",
    body_class: str = "",
    nav_active: str = "",
) -> HttpResponse:
    bootstrap = {
        "csrfToken": get_token(request),
        "user": _user_context(request.user),
        "nav": _nav_links(request.user, nav_active),
        # Present on every page so the footer can link the Privacy Policy and
        # Terms of Service from anywhere, signed in or not.
        "urls": {
            "logout": reverse("logout"),
            "privacy": reverse("privacy_policy"),
            "terms": reverse("terms_of_service"),
        },
        "messages": [
            {"level": message.level_tag, "text": message.message}
            for message in get_messages(request)
        ],
        "data": data or {},
    }

    return render(
        request,
        APP_TEMPLATE,
        {
            "page_title": title,
            "page_description": description,
            "body_class": body_class,
            "vite_entry": f"src/entries/{entry}.jsx",
            "bootstrap": bootstrap,
        },
    )
