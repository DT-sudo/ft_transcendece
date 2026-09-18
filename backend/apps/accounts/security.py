"""The security audit log, and ending the sessions an account no longer deserves.

Two jobs that belong together: whenever a session is cut short - a sign-out, a password
reset, a role change, an erased account - the reason goes to the `planshift.security`
logger, and every other tab the account has open is told to drop to the sign-in page.

Sessions live in `django.contrib.sessions` and hold only the signed user id, so finding
an account's sessions means decoding the unexpired ones. That is a table scan, which is
the right trade at this size: it happens on account writes, never on a page view.
"""

from __future__ import annotations

import logging

from django.contrib.auth import SESSION_KEY
from django.contrib.sessions.models import Session
from django.http import HttpRequest
from django.utils import timezone

from apps.realtime.events import SESSION_ENDED, push_to_user, send_to_session

logger = logging.getLogger("planshift.security")

# The session key holding the role the session was signed in with (see `SessionSecurityMiddleware`).
SESSION_ROLE_KEY = "auth_role"


def client_ip(request: HttpRequest | None) -> str:
    """The caller's address. nginx is the only proxy, so the first X-Forwarded-For entry is the client."""
    if request is None:
        return "-"
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return forwarded.split(",")[0].strip() or request.META.get("REMOTE_ADDR", "-")


def log_security(event: str, request: HttpRequest | None = None, *, actor=None, target=None, **fields) -> None:
    """One audit line: what happened, who did it, to whom, from where.

    Identities are logged as `id:username`, never as anything the account can type into
    its own profile, so a crafted name cannot forge a line.
    """

    def who(user) -> str:
        return f"{user.pk}:{user.get_username()}" if getattr(user, "pk", None) else "-"

    if actor is None and request is not None and getattr(request.user, "is_authenticated", False):
        actor = request.user
    parts = [f"event={event}", f"actor={who(actor)}", f"ip={client_ip(request)}"]
    if target is not None:
        parts.append(f"target={who(target)}")
    parts += [f"{name}={value}" for name, value in fields.items()]
    logger.info(" ".join(parts))


def _sessions_of(user_id: int) -> list[Session]:
    """The unexpired sessions signed in as `user_id`."""
    signed_id = str(user_id)
    return [
        session
        for session in Session.objects.filter(expire_date__gte=timezone.now())
        if session.get_decoded().get(SESSION_KEY) == signed_id
    ]


def end_sessions_for(user_id: int, *, reason: str, request: HttpRequest | None = None, keep: str | None = None) -> int:
    """Sign an account out everywhere, and tell the pages it has open to go to the sign-in page.

    `keep` is a session key to spare - the caller's own, when an account ends only its
    other sessions. Takes an id so it can also run for an account that was just erased.
    Returns how many sessions were deleted.
    """
    keys = [session.session_key for session in _sessions_of(user_id) if session.session_key != keep]
    if keys:
        Session.objects.filter(session_key__in=keys).delete()
    # Whether or not a session row was deleted, the open tabs are told: their next
    # request would only land on the sign-in page anyway.
    push_to_user(user_id, SESSION_ENDED)
    log_security("session.ended", request, reason=reason, account=user_id, sessions=len(keys))
    return len(keys)


def end_sessions(user, *, reason: str, request: HttpRequest | None = None, keep: str | None = None) -> int:
    """`end_sessions_for` for an account that still exists."""
    return end_sessions_for(user.pk, reason=reason, request=request, keep=keep)


def end_this_session(request: HttpRequest) -> None:
    """Tell the tabs of the caller's own browser session to go to the sign-in page.

    Signing out already invalidates the session for all of them server-side; this is what
    makes the tabs that are not doing the signing out notice, instead of sitting on a page
    that no longer loads.
    """
    if request.session.session_key:
        send_to_session(request.session.session_key, SESSION_ENDED)
