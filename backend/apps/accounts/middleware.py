"""Keep a signed-in page from outliving the session that was granted it.

Two guards that fail in the same way - the browser still showing a page the account is no
longer entitled to:

*Role changes.* A session is signed in as the role it had at sign-in. The admin can change
that role under it, and the pages of the old role are a different job entirely (an employee
must not keep a manager's calendar open). So the role is stamped on the session and checked
on every request; a session whose stamp no longer matches is signed out.

*The back button.* Without an explicit header the browser is free to keep a rendered page and
hand it back on Back - out of the back/forward cache, without asking the server. After
signing out, or after a role change, that shows a page the account can no longer load. Every
authenticated response therefore says `no-store`, which both bars the shared caches and takes
the page out of the back/forward cache, so Back re-requests it and lands on the sign-in page.
"""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import logout
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.utils.translation import gettext as _

from .security import SESSION_ROLE_KEY, log_security

# Nothing an account can be shown while signed in may be stored, by any cache.
NO_STORE = "no-store, no-cache, must-revalidate, private, max-age=0"


class SessionSecurityMiddleware:
    """Sign out a session whose role changed under it, and keep signed-in pages out of caches."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self._no_store(request, self._role_guard(request) or self.get_response(request))

    @staticmethod
    def _role_guard(request: HttpRequest) -> HttpResponse | None:
        """Sign out and send to the sign-in page when the session's role is no longer the account's."""
        user = request.user
        if not user.is_authenticated:
            return None

        stamped = request.session.get(SESSION_ROLE_KEY)
        if stamped is None:
            # First request of a session (and of any session predating this guard).
            request.session[SESSION_ROLE_KEY] = user.role
            return None
        if stamped == user.role:
            return None

        log_security("session.role_mismatch", request, actor=user, was=stamped, now=user.role)
        logout(request)
        messages.warning(request, _("Your role was changed. Please sign in again."))
        return redirect("login")

    @staticmethod
    def _no_store(request: HttpRequest, response: HttpResponse) -> HttpResponse:
        # A view that set its own policy knows better - the avatar stream caches on purpose.
        if getattr(request, "user", None) and request.user.is_authenticated and "Cache-Control" not in response:
            response["Cache-Control"] = NO_STORE
        return response
