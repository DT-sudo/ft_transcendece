"""Profile pictures: checked as images, then re-encoded to one small WebP.

Re-encoding from the decoded pixels drops EXIF metadata (camera, GPS position) and
anything a crafted file hides after the image data, so whatever was uploaded, the
stored file is a plain 256x256 WebP.
"""

from __future__ import annotations

from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

# Accepted uploads: Pillow's format name -> MIME type (the file input's `accept`).
FORMATS = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp", "GIF": "image/gif"}
MAX_BYTES = 2 * 1024 * 1024
MAX_SIDE = 4096
SIZE = 256


def to_webp(upload) -> ContentFile:
    """Center-crop and scale the upload (already verified by `AvatarForm`) to a SIZE x SIZE WebP."""
    upload.seek(0)
    with Image.open(upload) as image:
        upright = ImageOps.exif_transpose(image)  # phones store portraits sideways plus a rotation tag
        has_alpha = upright.mode in ("RGBA", "LA") or "transparency" in upright.info
        square = ImageOps.fit(upright.convert("RGBA" if has_alpha else "RGB"), (SIZE, SIZE), Image.Resampling.LANCZOS)
        buffer = BytesIO()
        square.save(buffer, "WEBP", quality=85)
    return ContentFile(buffer.getvalue())


def replace_avatar(user, content: ContentFile | None) -> None:
    """Store `content` as the user's picture (None removes it) and delete the file it replaces."""
    old = user.avatar.name
    if content is None:
        user.avatar = ""
    else:
        user.avatar.save("avatar.webp", content, save=False)  # `avatar_path` picks the real name
    user.save(update_fields=["avatar"])
    if old:
        user.avatar.storage.delete(old)
