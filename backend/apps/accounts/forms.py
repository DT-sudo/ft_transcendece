from __future__ import annotations

from django import forms
from django.contrib.auth.forms import AuthenticationForm, BaseUserCreationForm
from django.core.exceptions import ValidationError

from .models import User, UserRole


def _split_full_name(full_name: str) -> tuple[str, str]:
    first, _, last = (full_name or "").strip().partition(" ")
    return first, last.strip()


class EmailAuthenticationForm(AuthenticationForm):
    """Login by email address.

    Every account's `username` mirrors its lowercased email, so lowercasing the
    input and handing it to Django's default backend is the whole email login.
    """

    username = forms.EmailField(label="Email", max_length=254)

    error_messages = {**AuthenticationForm.error_messages, "invalid_login": "Incorrect email or password."}

    def clean_username(self) -> str:
        return (self.cleaned_data.get("username") or "").strip().lower()


class SignUpForm(BaseUserCreationForm):
    """Public registration of a manager account.

    Employees are provisioned by their manager, so the only account someone can
    open for themselves is a manager account. Django's creation form handles the
    two password fields and runs the password validators against the instance.
    """

    full_name = forms.CharField(label="Full name", max_length=150)

    class Meta:
        model = User
        fields = ["email"]

    def clean_full_name(self) -> str:
        full_name = " ".join((self.cleaned_data.get("full_name") or "").split())
        if len(full_name) < 2:
            raise ValidationError("Enter your full name.")
        return full_name

    def clean_email(self) -> str:
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise ValidationError("Email is required.")
        if User.objects.filter(username=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def _post_clean(self) -> None:
        # Fill the instance before the password validators run, so a password
        # similar to the name or email is caught.
        self.instance.first_name, self.instance.last_name = _split_full_name(self.cleaned_data.get("full_name", ""))
        self.instance.username = self.cleaned_data.get("email", "")
        self.instance.role = UserRole.MANAGER
        super()._post_clean()


class EmployeeForm(forms.ModelForm):
    """Manager-side create/edit of an employee; the view sets the role and password."""

    full_name = forms.CharField(label="Full name", max_length=150)

    class Meta:
        model = User
        fields = ["email", "position"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        self.fields["position"].required = True

    def clean_email(self) -> str:
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if User.objects.filter(username=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("An employee with this email already exists.")
        return email

    def save(self, commit=True) -> User:
        user = super().save(commit=False)
        user.first_name, user.last_name = _split_full_name(self.cleaned_data["full_name"])
        user.username = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
