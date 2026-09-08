from __future__ import annotations

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect


def _redirect_with_message(
    request: HttpRequest,
    *,
    level: int,
    text: str,
    to: str = "manager_employees",
) -> HttpResponse:
    """Add a flash message and redirect; the message arrives as a toast."""
    messages.add_message(request, level, text)
    return redirect(to)


def _first_error(form, default: str) -> str:
    """First error message on a form, for flows that redirect instead of re-rendering."""
    for errors in form.errors.values():
        if errors:
            return errors[0]
    return default


def _field_errors(form) -> dict[str, str]:
    """Flatten a form's field errors into {field: first message} for React.

    The client validates the same rules before submitting; this is what the
    server sends back when its own validation is the one that rejects.
    """
    return {name: errors[0] for name, errors in form.errors.items() if errors}
