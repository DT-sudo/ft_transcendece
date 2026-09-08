"""Authentication: sign-up, login, logout and post-login routing."""

from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from apps.frontend.shell import render_app

from ..forms import EmailAuthenticationForm, SignUpForm
from .helpers import _field_errors


def _login_urls() -> dict[str, str]:
    urls = {"login": reverse("login"), "signup": reverse("signup")}
    if settings.ENABLE_DEMO_LOGIN:
        urls["demoManager"] = reverse("demo_login", args=["manager"])
        urls["demoEmployee"] = reverse("demo_login", args=["employee"])
    return urls


@require_http_methods(["GET", "POST"])
def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("home")

    form = EmailAuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("home")

    # AuthenticationForm calls the field `username`; the UI calls it `email`.
    field_errors = _field_errors(form)
    if "username" in field_errors:
        field_errors["email"] = field_errors.pop("username")

    return render_app(
        request,
        entry="login",
        title="Login",
        description="Shift Management System Login",
        body_class="auth-body",
        data={
            "showDemo": settings.ENABLE_DEMO_LOGIN,
            "email": form["username"].value() or "",
            "error": " ".join(form.non_field_errors()),
            "fieldErrors": field_errors,
            "urls": _login_urls(),
        },
    )


@require_http_methods(["GET", "POST"])
def signup_view(request: HttpRequest) -> HttpResponse:
    """Open a manager account: email + password, hashed by Django's PBKDF2."""
    if request.user.is_authenticated:
        return redirect("home")

    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user, backend="apps.accounts.auth_backends.EmailBackend")
        messages.success(request, f"Welcome, {user.get_full_name()}. Your account is ready.")
        return redirect("home")

    submitted = request.POST if request.method == "POST" else {}
    return render_app(
        request,
        entry="signup",
        title="Create account",
        description="Create a PlanShift manager account",
        body_class="auth-body",
        data={
            "values": {
                "fullName": submitted.get("full_name", ""),
                "email": submitted.get("email", ""),
            },
            "error": " ".join(form.non_field_errors()) if request.method == "POST" else "",
            "fieldErrors": _field_errors(form) if request.method == "POST" else {},
            "urls": {"signup": reverse("signup"), "login": reverse("login")},
        },
    )


@login_required
@require_POST
def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect("login")


@login_required
def home(request: HttpRequest) -> HttpResponse:
    """Send each role to its own landing page."""
    if request.user.is_manager:
        return redirect("manager_shifts")
    return redirect("employee_shifts")
