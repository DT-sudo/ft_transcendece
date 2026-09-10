from django import forms

from .models import Position, Shift


class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ["name"]


class ShiftForm(forms.ModelForm):
    """Shift fields only; assignments are validated separately by the scheduling rules."""

    class Meta:
        model = Shift
        fields = ["date", "start_time", "end_time", "position", "capacity"]
