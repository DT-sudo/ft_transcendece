from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User

from . import services, totp


def _code_field(required_message: str) -> forms.CharField:
    return forms.CharField(max_length=32, error_messages={"required": required_message})


class LoginCodeForm(forms.Form):
    code = _code_field(_("Enter the code from your authenticator app, or a recovery code."))


class ConfirmSetupForm(forms.Form):
    """The first code from the app proves it holds the secret before 2FA is switched on."""

    code = _code_field(_("Enter the 6-digit code your app shows."))

    def __init__(self, secret: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.secret = secret
        self.step: int | None = None

    def clean_code(self) -> str:
        code = services.normalize(self.cleaned_data["code"])
        self.step = totp.matching_step(self.secret, code) if totp.looks_like_code(code) else None
        if self.step is None:
            raise ValidationError(_("That code doesn't match. Check that your phone's clock is set automatically, then try the new code."))
        return code


class ReauthenticateForm(forms.Form):
    """Both factors again before 2FA is turned off or its recovery codes are replaced.

    The code is only checked once the password is right, so someone at an
    unlocked computer can't use up the attempts and lock the owner out.
    """

    password = forms.CharField(strip=False, error_messages={"required": _("Enter your password.")})
    code = _code_field(_("Enter a code from your app, or a recovery code."))

    def __init__(self, user: User, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self) -> dict:
        cleaned = super().clean()
        if "password" in cleaned and not self.user.check_password(cleaned["password"]):
            self.add_error("password", _("Your password is incorrect."))
        elif "password" in cleaned and "code" in cleaned:
            result = services.verify(self.user, cleaned["code"])
            if result is services.Result.LOCKED:
                self.add_error("code", services.LOCKED_MESSAGE)
            elif not result.ok:
                self.add_error("code", _("That code is not valid."))
        return cleaned
