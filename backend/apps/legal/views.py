"""Privacy Policy and Terms of Service.

Both are public: the subject requires them to be reachable from anywhere in the
application, including the login page, so they carry no auth decorator. The
prose lives in `documents.py` and is rendered by the shared React shell.
"""

from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_GET

from apps.frontend.shell import render_app


@require_GET
def legal_page(request: HttpRequest, document: dict) -> HttpResponse:
    return render_app(
        request,
        page="legal",
        title=document["title"],
        description=document["summary"],
        data={"document": document},
    )
