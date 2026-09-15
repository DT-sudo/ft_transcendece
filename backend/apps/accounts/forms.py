from __future__ import annotations

from django import forms
from django.contrib.auth.forms import AuthenticationForm, BaseUserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import User, UserRole


def _split_full_name(full_name: str) -> tuple[str, str]:
    first, _, last = (full_name or "").strip().partition(" ")
    return first, last.strip()


def clean_full_name(value: str | None) -> str:
    full_name = " ".join((value or "").split())
    if len(full_name) < 2:
        raise ValidationError(_("Enter your full name."))
    return full_name


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
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(username=email).exists():
            raise ValidationError(_("An account with this email already exists."))
        return email

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
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if User.objects.filter(username=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_("An account with this email already exists."))
        return email

    def save(self, commit=True) -> User:
        user = super().save(commit=False)
        user.first_name, user.last_name = _split_full_name(self.cleaned_data["full_name"])
        user.username = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class EmployeeForm(AccountForm):
    """Manager-side create/edit of an employee (the model's default role); the view sets the password."""

    class Meta:
        model = User
        fields = ["email", "position"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["position"].required = True


class UserForm(EmployeeForm):
    """Admin-side create/edit of any account: the role is picked too, and only employees have a position."""

    class Meta(EmployeeForm.Meta):
        fields = ["email", "role", "position"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["position"].required = False

    def clean(self) -> dict:
        cleaned = super().clean()
        role = cleaned.get("role")
        if role == UserRole.EMPLOYEE:
            if not cleaned.get("position"):
                self.add_error("position", _("Employees need a position."))
        elif role:
            cleaned["position"] = None

        # Managers own shifts and employees are assigned to them; switching sides would strand those shifts.
        # (`self.instance` still holds the saved role here: the posted one is copied onto it after clean().)
        switches_side = self.instance.pk and role and (role == UserRole.EMPLOYEE) != self.instance.is_employee
        if switches_side and (self.instance.created_shifts.exists() or self.instance.assignments.exists()):
            raise ValidationError(_("Reassign or remove this user's shifts before switching between employee and manager roles."))
        return cleaned
