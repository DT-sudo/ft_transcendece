"""`{% vite_asset %}`: the <link>/<script> tags for the single React entry.

In development, point VITE_DEV_SERVER_URL at `npm run dev` and the tag serves
the modules straight from Vite (with hot reload). Otherwise it reads
frontend/dist/.vite/manifest.json produced by `npm run build`.
"""

import json
from functools import lru_cache

from django import template
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.templatetags.static import static
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

register = template.Library()

ENTRY = "src/main.jsx"

REACT_REFRESH_PREAMBLE = """<script type="module">
  import RefreshRuntime from '{url}/@react-refresh';
  RefreshRuntime.injectIntoGlobalHook(window);
  window.$RefreshReg$ = () => {{}};
  window.$RefreshSig$ = () => (type) => type;
  window.__vite_plugin_react_preamble_installed__ = true;
</script>"""


@lru_cache(maxsize=1)
def _manifest() -> dict:
    path = settings.FRONTEND_DIST_DIR / ".vite" / "manifest.json"
    if not path.exists():
        raise ImproperlyConfigured(f"Vite manifest not found at {path}. Run `npm install && npm run build` in frontend/.")
    return json.loads(path.read_text())


@register.simple_tag
def vite_asset() -> str:
    dev_server = settings.VITE_DEV_SERVER_URL.rstrip("/")
    if dev_server:
        return format_html(
            "{}{}{}",
            mark_safe(REACT_REFRESH_PREAMBLE.format(url=dev_server)),
            format_html('<script type="module" src="{}/@vite/client"></script>', dev_server),
            format_html('<script type="module" src="{}/{}"></script>', dev_server, ENTRY),
        )

    if settings.DEBUG:
        _manifest.cache_clear()  # rebuilds are frequent in development
    chunk = _manifest()[ENTRY]
    links = format_html_join("\n", '<link rel="stylesheet" href="{}">', ((static(css),) for css in chunk.get("css", [])))
    return format_html('{}\n<script type="module" src="{}"></script>', links, static(chunk["file"]))
