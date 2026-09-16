from __future__ import annotations

from django import forms
from django.contrib.auth.forms import AuthenticationForm, BaseUserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import MANAGER_POSITION_NAME, Position, User, UserRole


def _split_full_name(full_name: str) -> tuple[str, str]:
    first, _, last = (full_name or "").strip().partition(" ")
    return first, last.strip()


def clean_full_name(value: str | None) -> str:
    full_name = " ".join((value or "").split())
    if len(full_name) < 2:
        raise ValidationError(_("Enter your full name."))
    return full_name


def _unique_email(value: str | None, instance: User) -> str:
    """The lowercased email, refused when another account already signs in with it."""
    email = (value or "").strip().lower()
    if User.objects.filter(username=email).exclude(pk=instance.pk).exists():
        raise ValidationError(_("An account with this email already exists."))
    return email


class EmailAuthenticationForm(AuthenticationForm):
    """Login by email address.

    Every account's `username` mirrors its lowercased email, so lowercasing the
    input and handing it to Django's default backend is the whole email login.
    """

    username = forms.EmailField(label=_("Email"), max_length=254)

    error_messages = {**AuthenticationForm.error_messages, "invalid_login": _("Incorrect email or password.")}

    def clean_username(self) -> str:
        return (self.cleaned_data.get("username") or "").strip().lower()


class SignUpForm(BaseUserCreationForm):
    """Public registration of a manager account.

    Employees are provisioned by their manager, so the only account someone can
    open for themselves is a manager account. Django's creation form handles the
    two password fields and runs the password validators against the instance.
    """

    full_name = forms.CharField(label=_("Full name"), max_length=150)

    class Meta:
        model = User
        fields = ["email"]

    def clean_full_name(self) -> str:
        return clean_full_name(self.cleaned_data.get("full_name"))

    def clean_email(self) -> str:
        return _unique_email(self.cleaned_data["email"], self.instance)

    def _post_clean(self) -> None:
        # Fill the instance before the password validators run, so a password
        # similar to the name or email is caught.
        self.instance.first_name, self.instance.last_name = _split_full_name(self.cleaned_data.get("full_name", ""))
        self.instance.username = self.cleaned_data.get("email", "")
        self.instance.role = UserRole.MANAGER
        super()._post_clean()


class AccountForm(forms.ModelForm):
    """Base for forms that set an account's name and email; the email doubles as the login username."""

    full_name = forms.CharField(label=_("Full name"), max_length=150)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True

    def clean_email(self) -> str:
        return _unique_email(self.cleaned_data.get("email"), self.instance)

    def save(self, commit=True) -> User:
        user = super().save(commit=False)
        user.first_name, user.last_name = _split_full_name(self.cleaned_data["full_name"])
        user.username = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ["name"]
        error_messages = {
            "name": {
                "required": _("Enter a position name."),
                "unique": _("A position with this name already exists."),
            }
        }


class UserForm(AccountForm):
    """The admin's create/edit of any account: a role is picked, and only employees have a position.

    Giving an employee the permanent "Manager" position promotes them instead of assigning a job
    title: `save()` swaps it for `role=MANAGER` and clears the position, since managers don't work
    shifts.
    """

    class Meta:
        model = User
        fields = ["email", "role", "position"]

    def clean(self) -> dict:
        cleaned = super().clean()
        role, position = cleaned.get("role"), cleaned.get("position")
        if role == UserRole.EMPLOYEE:
            if not position:
                self.add_error("position", _("Employees need a position."))
            elif position.name == MANAGER_POSITION_NAME and self.instance.pk and self.instance.assignments.exists():
                self.add_error("position", _("Reassign or remove this employee's shifts before making them a manager."))
        elif role:
            cleaned["position"] = None

        # Managers own shifts and employees are assigned to them; switching sides would strand those shifts.
        # (`self.instance` still holds the saved role here: the posted one is copied onto it after clean().)
        switches_side = self.instance.pk and role and (role == UserRole.EMPLOYEE) != self.instance.is_employee
        if switches_side and (self.instance.created_shifts.exists() or self.instance.assignments.exists()):
            raise ValidationError(_("Reassign or remove this user's shifts before switching between employee and manager roles."))
        return cleaned

    def save(self, commit=True) -> User:
        user = super().save(commit=False)
        position = self.cleaned_data.get("position")
        self.promoted = bool(position and position.name == MANAGER_POSITION_NAME)
        if self.promoted:
            user.role = UserRole.MANAGER
            user.position = None
        if commit:
            user.save()
        return user
