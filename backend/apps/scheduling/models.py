from __future__ import annotations

from datetime import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class ShiftStatus(models.TextChoices):
    DRAFT = "draft", _("Draft")
    PUBLISHED = "published", _("Published")

class Shift(models.Model):
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    position = models.ForeignKey(
        "accounts.Position",
        on_delete=models.PROTECT,
        related_name="shifts"
    )
    capacity = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20, 
        choices=ShiftStatus.choices, 
        default=ShiftStatus.DRAFT
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_shifts",
    )
    # Bumped on every edit. The form sends the version it was opened on, so a save over
    # someone else's newer edit is refused instead of silently overwriting it.
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["date", "start_time"]

    def clean(self) -> None:
        errors = {}
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            errors["end_time"] = _("End time must be after start time.")
        if self.capacity is not None and self.capacity < 1:
            errors["capacity"] = _("Capacity must be at least 1.")
        if errors:
            raise ValidationError(errors)

    @property
    def is_past(self) -> bool:
        dt_end = datetime.combine(self.date, self.end_time, tzinfo=timezone.get_current_timezone())
        return dt_end < timezone.now()

class Assignment(models.Model):

    shift = models.ForeignKey(
        Shift, 
        on_delete=models.CASCADE,
        related_name="assignments"
    )
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name="assignments"
    )
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["shift", "employee"], 
                name="unique_employee_per_shift"
            ),
        ]

class EmployeeUnavailability(models.Model):
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="unavailability",
    )
    date = models.DateField(db_index=True)

    class Meta:
        ordering = ["date"]
        constraints = [
            models.UniqueConstraint(
                fields=["employee", "date"], 
                name="unique_employee_unavailability_day"
            ),
        ]
