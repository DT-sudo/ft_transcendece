from __future__ import annotations

from django.conf import settings
from django.db import models
from django.db.models.functions import Greatest, Least


class FriendshipStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"


class Friendship(models.Model):
    """One row per pair of users: `from_user` asked, `to_user` answers.

    Declining, cancelling and unfriending all delete the row, so a pair can start over.
    """

    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="friend_requests_sent"
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="friend_requests_received"
    )
    status = models.CharField(max_length=10, choices=FriendshipStatus.choices, default=FriendshipStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            # One row per pair whichever way round it was asked: A -> B also blocks B -> A.
            models.UniqueConstraint(Least("from_user", "to_user"), Greatest("from_user", "to_user"), name="unique_friendship_pair"),
            models.CheckConstraint(condition=~models.Q(from_user=models.F("to_user")), name="no_self_friendship"),
        ]

    @property
    def accepted(self) -> bool:
        return self.status == FriendshipStatus.ACCEPTED

    def other(self, user):
        """The person on the other side from `user`."""
        return self.to_user if self.from_user_id == user.pk else self.from_user
