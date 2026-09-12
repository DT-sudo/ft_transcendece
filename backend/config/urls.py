import re

from django.contrib import admin
from django.contrib.staticfiles.views import serve as serve_static
from django.urls import include, path, re_path
from django.conf import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.accounts.urls")),
    path("", include("apps.legal.urls")),
    path("", include("apps.scheduling.urls")),
]

# Serve the built Vite bundle (frontend/dist, via STATICFILES_DIRS) ourselves,
# regardless of DEBUG: nginx proxies every request straight to Django (see
# docker/nginx/nginx.conf.template) rather than serving /static/ itself, and
# there is no collectstatic/WhiteNoise step in the deploy pipeline. Without
# this, `staticfiles`'s serve() view 404s on every asset whenever DEBUG=0
# (its default guard against serving static files outside development),
# leaving the page's JS/CSS unresolved and `<div id="root">` empty.
# `insecure=True` is Django's own documented escape hatch for exactly this —
# "serve static files even if DEBUG is False" — and is in keeping with this
# project's demo/eval-only deployment (self-signed TLS, no reverse-proxy
# static serving) rather than a hardened production setup.
if not settings.VITE_DEV_SERVER_URL:
    urlpatterns += [
        re_path(
            r"^%s(?P<path>.*)$" % re.escape(settings.STATIC_URL.lstrip("/")),
            serve_static,
            kwargs={"insecure": True},
        ),
    ]
