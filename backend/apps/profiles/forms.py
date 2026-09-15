from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.accounts.forms import AccountForm, clean_full_name
from apps.accounts.models import User

from . import avatars


class ProfileForm(AccountForm):
    """Your own name, email and bio. Changing the email (it is also the login) takes the current password."""

    current_password = forms.CharField(required=False, strip=False, widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["email", "bio"]

    def clean_full_name(self) -> str:
        return clean_full_name(self.cleaned_data.get("full_name"))

    def clean(self) -> dict:
        cleaned = super().clean()
        # `self.instance` still holds the saved email here: the posted one is copied onto it after clean().
        email_changed = cleaned.get("email") and cleaned["email"] != self.instance.email
        if email_changed and not self.instance.check_password(cleaned.get("current_password") or ""):
            self.add_error("current_password", _("Enter your current password to change your email."))
        return cleaned


class AvatarForm(forms.Form):
    # Django's ImageField has Pillow open and verify the file, so a renamed text file is refused.
    avatar = forms.ImageField(
        error_messages={
            "required": _("Choose a picture to upload."),
            "invalid_image": _("That file isn't a picture we can read. Use JPEG, PNG, WebP or GIF."),
        }
    )

    def clean_avatar(self):
        upload = self.cleaned_data["avatar"]
        if upload.size > avatars.MAX_BYTES:
            raise ValidationError(_("The picture must be %(size)d MB or smaller.") % {"size": avatars.MAX_BYTES // 2**20})
        if upload.image.format not in avatars.FORMATS:
            raise ValidationError(_("Use a JPEG, PNG, WebP or GIF picture."))
        if max(upload.image.size) > avatars.MAX_SIDE:
            raise ValidationError(_("The picture must be at most %(pixels)d pixels on each side.") % {"pixels": avatars.MAX_SIDE})
        return upload
