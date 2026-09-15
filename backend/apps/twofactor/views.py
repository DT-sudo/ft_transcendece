"""The sign-in code step, and the Security card of Account settings (the "Minor: 2FA" module)."""

from __future__ import annotations

import time
from typing import Any

from django.contrib import messages
from django.contrib.auth import login
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.translation import ngettext
from django.views.decorators.http import require_http_methods, require_POST

from apps.accounts.models import User
from apps.shell import field_errors, flash_redirect, render_app

from . import services, totp
from .forms import ConfirmSetupForm, LoginCodeForm, ReauthenticateForm

# A password was right but the code is still owed: who, with which auth backend, since when.
PENDING_LOGIN = "twofactor_pending_login"
PENDING_LOGIN_SECONDS = 5 * 60
# The secret being set up, until the app's first code confirms it, then the new recovery codes (shown once).
SETUP_SECRET = "twofactor_setup_secret"
NEW_RECOVERY_CODES = "twofactor_recovery_codes"


# ── Sign-in ─────────────────────────────────────────────────────────────────


def begin_login(request: HttpRequest, user: User) -> HttpResponse:
    """Sign in someone who got past the password (or a demo button); with 2FA on, only after the code step."""
    backend = getattr(user, "backend", None)
    if not services.is_enabled(user):
        login(request, user, backend=backend)
        return redirect("home")
    request.session[PENDING_LOGIN] = {"user_id": user.pk, "backend": backend, "started": time.time()}
    return redirect("login_verify")


def _pending_user(request: HttpRequest) -> User | None:
    pending = request.session.get(PENDING_LOGIN)
    if not pending or time.time() - pending["started"] > PENDING_LOGIN_SECONDS:
        return None
    return User.objects.filter(pk=pending["user_id"], is_active=True).first()


@require_http_methods(["GET", "POST"])
def login_verify(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("home")

    user = _pending_user(request)
    if user is None or not services.is_enabled(user):
        if request.session.pop(PENDING_LOGIN, None):
            messages.error(request, _("Your sign-in timed out. Enter your password again."))
        return redirect("login")

    form = LoginCodeForm(request.POST or None)
    error = ""
    if request.method == "POST" and form.is_valid():
        result = services.verify(user, form.cleaned_data["code"])
        if result is services.Result.LOCKED:
            del request.session[PENDING_LOGIN]
            return flash_redirect(request, messages.ERROR, services.LOCKED_MESSAGE, "login")
        if result.ok:
            login(request, user, backend=request.session.pop(PENDING_LOGIN)["backend"])
            if result is services.Result.RECOVERY_CODE:
                left = services.recovery_codes_left(user)
                messages.warning(
                    request,
                    ngettext(
                        "You signed in with a recovery code, which now no longer works. %(count)d left: "
                        "get new ones in Account settings if you're running out.",
                        "You signed in with a recovery code, which now no longer works. %(count)d left: "
                        "get new ones in Account settings if you're running out.",
                        left,
                    )
                    % {"count": left},
                )
            return redirect("home")
        error = _("That code is not valid. Try again.")
    elif request.method == "POST":
        error = field_errors(form).get("code", "")

    return render_app(
        request,
        page="two-factor-verify",
        title=_("Two-factor authentication"),
        data={
            "email": user.email,
            "error": error,
            "useRecoveryCode": request.POST.get("mode") == "recovery",
            "urls": {"verify": reverse("login_verify"), "cancel": reverse("login_verify_cancel")},
        },
    )


@require_POST
def login_verify_cancel(request: HttpRequest) -> HttpResponse:
    request.session.pop(PENDING_LOGIN, None)
    return redirect("login")


# ── Account settings: the Security card ─────────────────────────────────────

SETTINGS_SECTIONS = {"2fa_start", "2fa_cancel", "2fa_confirm", "2fa_disable", "2fa_recovery"}


def settings_action(request: HttpRequest, section: str) -> tuple[HttpResponse | None, dict[str, str]]:
    """Handle a Security card POST: a redirect when done, otherwise the field errors to show in place."""
    user = request.user
    back = reverse("account_settings") + "#security"
    enabled = services.is_enabled(user)
    secret = request.session.get(SETUP_SECRET)

    if section == "2fa_start" and not enabled:
        request.session[SETUP_SECRET] = totp.new_secret()
    elif section == "2fa_cancel":
        request.session.pop(SETUP_SECRET, None)
    elif section == "2fa_confirm" and not enabled and secret:
        form = ConfirmSetupForm(secret, request.POST)
        if not form.is_valid():
            return None, field_errors(form)
        request.session[NEW_RECOVERY_CODES] = services.enable(user, secret, form.step)
        del request.session[SETUP_SECRET]
        return flash_redirect(request, messages.SUCCESS, _("Two-factor authentication is on."), back), {}
    elif section in ("2fa_disable", "2fa_recovery") and enabled:
        form = ReauthenticateForm(user, request.POST)
        if not form.is_valid():
            return None, field_errors(form)
        if section == "2fa_disable":
            services.disable(user)
            return flash_redirect(request, messages.SUCCESS, _("Two-factor authentication is off."), back), {}
        request.session[NEW_RECOVERY_CODES] = services.replace_recovery_codes(user)
        return flash_redirect(request, messages.SUCCESS, _("New recovery codes created. The old ones no longer work."), back), {}
    # Starting, cancelling, or a form left stale by another tab: just show the card as it now is.
    return redirect(back), {}


def settings_data(request: HttpRequest, errors: dict[str, str]) -> dict[str, Any]:
    user = request.user
    enabled = services.is_enabled(user)
    secret = None if enabled else request.session.get(SETUP_SECRET)
    setup = None
    if secret:
        uri = totp.provisioning_uri(secret, user.email)
        setup = {"secret": secret, "qr": totp.qr_data_uri(uri), "uri": uri}
    return {
        "enabled": enabled,
        "enabledAt": user.totp_device.confirmed_at.isoformat() if enabled else None,
        "recoveryCodesLeft": services.recovery_codes_left(user) if enabled else 0,
        "setup": setup,
        # Present once, right after they were created.
        "recoveryCodes": request.session.pop(NEW_RECOVERY_CODES, None),
        "errors": errors,
    }
