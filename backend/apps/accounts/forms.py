from __future__ import annotations

from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from apps.scheduling.models import Position

from .models import User, UserRole

def _split_full_name(full_name: str) -> tuple[str, str]:
    parts = (full_name or "").split()
    first_name = parts[0] if parts else ""
    last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
    return first_name, last_name

class EmployeeBaseForm(forms.ModelForm):
    full_name = forms.CharField(label="Full name", max_length=150)

    class Meta:
        model = User
        fields = ["email", "position"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        self.fields["position"].queryset = Position.objects.order_by("name")
        self.fields["position"].required = True

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise ValidationError("Email is required.")
        qs = User.objects.filter(email=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("An employee with this email already exists.")
        return email

    def _apply_full_name(self, user: User) -> None:
        first_name, last_name = _split_full_name(self.cleaned_data.get("full_name"))
        user.first_name = first_name
        user.last_name = last_name

    def _apply_common(self, user: User) -> None:
        user.username = self.cleaned_data["email"]

    def save(self, commit=True) -> User:
        user: User = super().save(commit=False)
        self._apply_full_name(user)
        self._apply_common(user)
        if commit:
            user.save()
        return user

class CreateEmployeeForm(EmployeeBaseForm):
    def save(self, commit=True) -> User:
        user: User = super().save(commit=False)
        user.role = UserRole.EMPLOYEE
        user.is_staff = False
        user.is_superuser = False

        if commit:
            user.save()
        return user

class UpdateEmployeeForm(EmployeeBaseForm):
    pass


class EmailAuthenticationForm(AuthenticationForm):
    """Login by email address.

    `AuthenticationForm` hands its `username` field straight to `authenticate()`,
    which the EmailBackend reads as an email. Relabelling the field and swapping
    the widget is enough to make the whole flow email-based while keeping
    Django's rate-limit-friendly error handling and inactive-user check.
    """

    username = forms.EmailField(
        label="Email",
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email", "autofocus": True}),
    )

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Incorrect email or password.",
    }

    def clean_username(self) -> str:
        return (self.cleaned_data.get("username") or "").strip().lower()


class SignUpForm(forms.ModelForm):
    """Public registration.

    Employees are provisioned by their manager, so the only account someone can
    open for themselves is a manager account — a new team owner who then adds
    their own staff. `username` mirrors the email so both auth backends and the
    Django admin resolve the same person.
    """

    full_name = forms.CharField(label="Full name", max_length=150)
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput, strip=False)
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput, strip=False)

    class Meta:
        model = User
        fields = ["email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True

    def clean_full_name(self) -> str:
        full_name = " ".join((self.cleaned_data.get("full_name") or "").split())
        if len(full_name) < 2:
            raise ValidationError("Enter your full name.")
        return full_name

    def clean_email(self) -> str:
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if User.objects.filter(email__iexact=email).exists() or User.objects.filter(username=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def clean_password2(self) -> str:
        password1 = self.cleaned_data.get("password1") or ""
        password2 = self.cleaned_data.get("password2") or ""
        if password1 != password2:
            raise ValidationError("The two passwords do not match.")
        return password2

    def _post_clean(self) -> None:
        super()._post_clean()

        password = self.cleaned_data.get("password1")
        if not password:
            return

        # UserAttributeSimilarityValidator compares the password against fields
        # on the instance, so populate the name and username first — otherwise
        # it can only see the email and misses "jane doe" style passwords.
        full_name = self.cleaned_data.get("full_name")
        if full_name:
            self.instance.first_name, self.instance.last_name = _split_full_name(full_name)
        if self.cleaned_data.get("email"):
            self.instance.username = self.cleaned_data["email"]

        try:
            password_validation.validate_password(password, self.instance)
        except ValidationError as error:
            self.add_error("password1", error)

    def save(self, commit=True) -> User:
        user: User = super().save(commit=False)
        first_name, last_name = _split_full_name(self.cleaned_data["full_name"])
        user.first_name = first_name
        user.last_name = last_name
        user.username = self.cleaned_data["email"]
        user.role = UserRole.MANAGER
        user.is_staff = False
        user.is_superuser = False
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user
