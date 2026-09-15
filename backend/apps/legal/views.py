"""Privacy Policy and Terms of Service.

Both are public: the subject requires them to be reachable from anywhere in the
application, including the login page, so they carry no auth decorator. The
prose lives in `content/<language>.py` and is rendered by the shared React shell.
"""

from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_GET

from apps.shell import render_app

from .documents import document as legal_document


@require_GET
def legal_page(request: HttpRequest, name: str) -> HttpResponse:
    """The document in the reader's language."""
    document = legal_document(name)
    return render_app(
        request,
        page="legal",
        title=document["title"],
        data={"document": document},
    )
