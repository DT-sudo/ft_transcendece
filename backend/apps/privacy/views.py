"""Self-service GDPR endpoints (the "Minor: GDPR compliance features" module).

Every signed-in user - manager or employee - can reach these from the
account menu: see what personal data is held about them, download it in a
readable format, and delete their own account. See also
`apps.legal.documents` for the Privacy Policy text this implements, and
`apps.accounts.views` for the admin-initiated equivalent (deleting an
account, which already existed before this module).
"""

from __future__ import annotations

import json

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET, require_POST

from apps.accounts.services import release_from_upcoming
from apps.notifications.services import recent_notifications
from apps.profiles.services import involving
from apps.scheduling.models import Assignment, EmployeeUnavailability, Shift
from apps.scheduling.services import shift_fields
from apps.shell import render_app
from apps.twofactor.services import export_data as two_factor_export

from .emails import send_account_deleted_email, send_data_export_email


def _collect_user_data(user) -> dict:
    """Every piece of personal data this instance holds about `user` -
    matches what Privacy Policy section 1 ("Data we collect") describes."""
    data = {
        "exported_at": timezone.now().isoformat(),
        "account": {
            "employee_id": user.employee_id,
            "full_name": user.get_full_name(),
            "email": user.email,
            "role": user.get_role_display(),
            "position": user.position.name if user.position else None,
            "bio": user.bio,
            "profile_picture": _("uploaded (stored as a 256x256 WebP)") if user.avatar else None,
            "date_joined": user.date_joined.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "last_seen_online": user.last_seen.isoformat() if user.last_seen else None,
            "language": user.language,
        },
        "two_factor_authentication": two_factor_export(user),
    }
    data["friends"] = [
        {
            "name": friendship.other(user).display_name,
            "status": friendship.status,
            "requested_by": "you" if friendship.from_user_id == user.pk else "them",
            "since": (friendship.accepted_at or friendship.created_at).isoformat(),
        }
        for friendship in involving(user).select_related("from_user", "to_user").order_by("created_at")
    ]

    if user.is_employee:
        assignments = (
            Assignment.objects.filter(employee=user)
            .select_related("shift")
            .order_by("shift__date", "shift__start_time")
        )
        data["assigned_shifts"] = [{**shift_fields(a.shift), "status": a.shift.status} for a in assignments]
        data["unavailability"] = [
            date.isoformat()
            for date in EmployeeUnavailability.objects.filter(employee=user).order_by("date").values_list(
                "date", flat=True
            )
        ]
    else:
        created = Shift.objects.filter(created_by=user).order_by("date", "start_time")
        data["shifts_created"] = [
            {**shift_fields(shift), "status": shift.status, "capacity": shift.capacity} for shift in created
        ]

    data["notifications"] = recent_notifications(user, limit=None)
    return data


@login_required
@require_GET
def privacy_center(request: HttpRequest) -> HttpResponse:
    return render_app(
        request,
        page="privacy-center",
        title=_("Privacy & My Data"),
        data={
            "email": request.user.email,
            "isManager": request.user.is_manager,
            "urls": {
                "exportData": reverse("privacy_export_data"),
                "deleteAccount": reverse("privacy_delete_account"),
            },
        },
    )


@login_required
@require_GET
def export_my_data(request: HttpRequest) -> HttpResponse:
    """A readable (indented) JSON download of everything held about the caller."""
    user = request.user
    payload = json.dumps(_collect_user_data(user), indent=2, cls=DjangoJSONEncoder, ensure_ascii=False)

    send_data_export_email(user)

    response = HttpResponse(payload, content_type="application/json")
    filename = f"planshift-my-data-{timezone.localdate().isoformat()}.json"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
@require_POST
def delete_my_account(request: HttpRequest) -> HttpResponse:
    """Delete the caller's own account. Requires typing the account's email
    and its password - an in-app confirmation step, distinct from the
    confirmation *email* sent afterwards once deletion has actually happened.
    """
    user = request.user
    confirm_email = (request.POST.get("confirm_email") or "").strip().lower()
    confirm_password = request.POST.get("confirm_password") or ""

    if confirm_email != (user.email or "").strip().lower() or not user.check_password(confirm_password):
        messages.error(request, _("Email or password didn't match - account not deleted."))
        return redirect("privacy_center")

    email, name, language = user.email, user.display_name, user.language

    # The managers learn which upcoming shifts just lost a worker. The shifts a manager
    # wrote stay on the shared schedule, no longer linked to anyone.
    release_from_upcoming(user, actor=user, tell_account=False)
    user.delete()

    logout(request)
    send_account_deleted_email(email, name, language)
    messages.success(request, _("Your account and all associated data have been deleted."))
    return redirect("login")
