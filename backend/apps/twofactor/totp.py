"""Time-based one-time passwords (RFC 6238), the codes authenticator apps show.

Both sides share a random secret. Every 30 seconds (a "step") each derives a
6-digit code from HMAC-SHA1(secret, step number), so the server can check a
code without anything being sent to the phone.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote, urlencode

import segno

ISSUER = "PlanShift"
DIGITS = 6
STEP_SECONDS = 30
# Also accept the codes just before and after the current one, for clock drift and slow typing.
WINDOW = 1


def looks_like_code(code: str) -> bool:
    """Six digits: what an authenticator app shows, as opposed to a recovery code."""
    return code.isdigit() and len(code) == DIGITS


def new_secret() -> str:
    """160 random bits (the size RFC 4226 recommends), base32 as authenticator apps expect."""
    return base64.b32encode(secrets.token_bytes(20)).decode()


def current_step(now: float | None = None) -> int:
    return int((time.time() if now is None else now) // STEP_SECONDS)


def code_at(secret: str, step: int) -> str:
    digest = hmac.new(base64.b32decode(secret), struct.pack(">Q", step), hashlib.sha1).digest()
    # Dynamic truncation (RFC 4226 §5.3): the last nibble picks where to read 31 bits from.
    offset = digest[-1] & 0x0F
    number = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(number % 10**DIGITS).zfill(DIGITS)


def matching_step(secret: str, code: str, *, after: int = -1, now: float | None = None) -> int | None:
    """The step whose code this is, within the window and later than `after`; None if there is none.

    `after` is the last step already used, so a code that signed someone in can't be replayed.
    """
    step = current_step(now)
    for candidate in range(step - WINDOW, step + WINDOW + 1):
        if candidate > after and hmac.compare_digest(code_at(secret, candidate), code):
            return candidate
    return None


def provisioning_uri(secret: str, account: str) -> str:
    """The otpauth:// link a QR code carries (Google Authenticator's "Key Uri Format")."""
    label = quote(f"{ISSUER}:{account}")
    params = urlencode({"secret": secret, "issuer": ISSUER, "digits": DIGITS, "period": STEP_SECONDS})
    return f"otpauth://totp/{label}?{params}"


def qr_data_uri(uri: str) -> str:
    """The link as an SVG QR code, inlined as a data: URI so no image endpoint is needed."""
    return segno.make(uri, error="m").svg_data_uri(scale=5, border=2)
