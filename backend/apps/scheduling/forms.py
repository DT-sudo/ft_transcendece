from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Position, Shift


class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ["name"]
        error_messages = {
            "name": {
                "required": _("Enter a position name."),
                "unique": _("A position with this name already exists."),
            }
        }


class ShiftForm(forms.ModelForm):
    """Shift fields only; assignments are validated separately by the scheduling rules."""

    class Meta:
        model = Shift
        fields = ["date", "start_time", "end_time", "position", "capacity"]
