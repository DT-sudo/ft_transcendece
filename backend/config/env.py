"""Tiny `.env` loader: `KEY=value` lines, `#` comments. Real environment variables win."""

import os
from pathlib import Path


def load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.strip().partition("=")
        if sep and not key.startswith("#"):
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    return raw in {"1", "true", "yes", "on"} if raw else default


def env_list(name: str, default: list[str]) -> list[str]:
    values = [item.strip() for item in os.environ.get(name, "").split(",") if item.strip()]
    return values or default
