from __future__ import annotations

from django.conf import settings
from django.db import models

from .messages import RENDERERS, render


class Notification(models.Model):
    """One message to one user about something another user did."""

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    level = models.CharField(max_length=10, default="info")
    # What happened (a key of `messages.RENDERERS`) and the facts to say it with, so the text is
    # written in whatever language the reader uses when they read it. Facts, not links: the
    # shift or employee they name may be deleted later.
    kind = models.CharField(max_length=40, blank=True)
    params = models.JSONField(default=dict, blank=True)
    # The English text, kept as a readable record (and all older rows have).
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["recipient", "read_at"])]

    def text(self) -> tuple[str, str]:
        """Title and description in the active language."""
        if self.kind in RENDERERS:
            return render(self.kind, self.params)
        return self.title, self.description

    def as_dict(self) -> dict:
        """The shape the header bell renders."""
        title, description = self.text()
        return {
            "id": self.id,
            "level": self.level,
            "title": title,
            "description": description,
            "time": self.created_at.isoformat(),
            "read": self.read_at is not None,
        }
