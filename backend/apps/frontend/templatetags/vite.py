"""Template tag that turns Vite's build manifest into <script>/<link> tags.

In development, point VITE_DEV_SERVER_URL at `npm run dev` and the tag serves
the modules straight from Vite (with hot reload). Otherwise it reads
frontend/dist/.vite/manifest.json produced by `npm run build`.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from django import template
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.templatetags.static import static
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

register = template.Library()

REACT_REFRESH_PREAMBLE = """<script type="module">
  import RefreshRuntime from '{url}/@react-refresh';
  RefreshRuntime.injectIntoGlobalHook(window);
  window.$RefreshReg$ = () => {{}};
  window.$RefreshSig$ = () => (type) => type;
  window.__vite_plugin_react_preamble_installed__ = true;
</script>"""


def _manifest_path() -> Path:
    return settings.FRONTEND_DIST_DIR / ".vite" / "manifest.json"


@lru_cache(maxsize=1)
def _cached_manifest() -> dict:
    path = _manifest_path()
    if not path.exists():
        raise ImproperlyConfigured(
            f"Vite manifest not found at {path}. Run `npm install && npm run build` in frontend/."
        )
    return json.loads(path.read_text())


def _manifest() -> dict:
    # Rebuilds are frequent in development, so never serve a stale manifest there.
    if settings.DEBUG:
        _cached_manifest.cache_clear()
    return _cached_manifest()


def _walk_chunks(manifest: dict, entry: str, seen: set[str]) -> list[dict]:
    """The entry chunk plus every chunk it imports, depth first."""
    if entry in seen or entry not in manifest:
        return []

    seen.add(entry)
    chunk = manifest[entry]
    chunks = [chunk]
    for name in chunk.get("imports", []):
        chunks.extend(_walk_chunks(manifest, name, seen))
    return chunks


def _assets(manifest: dict, entry: str) -> tuple[list[str], list[str]]:
    """Stylesheets and preloadable chunk files reachable from an entry."""
    stylesheets: list[str] = []
    preloads: list[str] = []

    for index, chunk in enumerate(_walk_chunks(manifest, entry, set())):
        for css in chunk.get("css", []):
            if css not in stylesheets:
                stylesheets.append(css)
        if index and chunk["file"] not in preloads:
            preloads.append(chunk["file"])

    return stylesheets, preloads


@register.simple_tag
def vite_asset(entry: str) -> str:
    """Render the tags loading one Vite entry, e.g. "src/entries/login.jsx"."""
    dev_server = getattr(settings, "VITE_DEV_SERVER_URL", "").rstrip("/")
    if dev_server:
        return format_html(
            "{}{}{}",
            mark_safe(REACT_REFRESH_PREAMBLE.format(url=dev_server)),
            format_html('<script type="module" src="{}/@vite/client"></script>', dev_server),
            format_html('<script type="module" src="{}/{}"></script>', dev_server, entry),
        )

    manifest = _manifest()
    if entry not in manifest:
        raise ImproperlyConfigured(f"Unknown Vite entry '{entry}'. Rebuild the frontend.")

    stylesheets, preloads = _assets(manifest, entry)
    links = format_html_join(
        "\n",
        '<link rel="stylesheet" href="{}">',
        ((static(css),) for css in stylesheets),
    )
    preload_links = format_html_join(
        "\n",
        '<link rel="modulepreload" href="{}">',
        ((static(chunk),) for chunk in preloads),
    )
    script = format_html('<script type="module" src="{}"></script>', static(manifest[entry]["file"]))
    return format_html("{}\n{}\n{}", links, preload_links, script)
