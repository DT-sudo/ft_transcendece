"""Minimal `.env` loader.

The subject requires credentials to live in a git-ignored `.env` file, so the
settings module needs to read one before it looks at `os.environ`. Rather than
pull in a dependency for ~30 lines, we parse the file ourselves: `KEY=value`
per line, `#` comments, optional `export` prefix and optional surrounding
quotes. Real environment variables always win, so `docker compose` overrides
and shell exports keep their usual precedence.
"""

from __future__ import annotations

import os
from pathlib import Path


def load_dotenv(path: Path) -> None:
    if not path.is_file():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()

        key, separator, value = line.partition("=")
        if not separator:
            continue

        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]

        os.environ.setdefault(key, value)


def env_bool(name: str, default: bool) -> bool:
    """Read a boolean flag; accepts 1/true/yes/on (case-insensitive)."""
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: list[str]) -> list[str]:
    """Read a comma-separated list, dropping empty entries."""
    values = [item.strip() for item in os.environ.get(name, "").split(",")]
    return [item for item in values if item] or default
