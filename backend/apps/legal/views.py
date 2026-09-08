"""Privacy Policy and Terms of Service.

Both are public: the subject requires them to be reachable from anywhere in the
application, including the login page, so they carry no auth decorator. The
prose lives in `documents.py` and is rendered by the shared React shell, which
means these pages get the same header, footer and styling as the rest of the
app instead of being bolted-on static HTML.
"""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_GET

from apps.frontend.shell import render_app

from .documents import PRIVACY_POLICY, TERMS_OF_SERVICE


def _render(request: HttpRequest, document: dict) -> HttpResponse:
    return render_app(
        request,
        entry="legal",
        title=document["title"],
        description=document["summary"],
        data={"document": document},
    )


@require_GET
def privacy_policy(request: HttpRequest) -> HttpResponse:
    return _render(request, PRIVACY_POLICY)


@require_GET
def terms_of_service(request: HttpRequest) -> HttpResponse:
    return _render(request, TERMS_OF_SERVICE)
