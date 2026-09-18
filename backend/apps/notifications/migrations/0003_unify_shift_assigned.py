from django.db import migrations

# Keys of the shift details notifications used to keep, and the `shift_fields` names they now use.
RENAMED = {"start": "start_time", "end": "end_time"}


def _renamed(value):
    """`value` with every shift's old time keys renamed, however deep it sits in the params."""
    if isinstance(value, list):
        return [_renamed(item) for item in value]
    if isinstance(value, dict):
        return {RENAMED.get(key, key) if "position" in value else key: _renamed(item) for key, item in value.items()}
    return value


def unify(apps, schema_editor):
    """"A shift was published to you" and "you were added to a shift" now read the same, as
    "shift.assigned" over a list of shifts; shift details use the scheduling field names."""
    Notification = apps.get_model("notifications", "Notification")
    Notification.objects.filter(kind="shift.published").update(kind="shift.assigned")
    for notification in Notification.objects.filter(kind__startswith="shift.") | Notification.objects.filter(
        kind="position.shifts_cancelled"
    ):
        params = notification.params
        if notification.kind == "shift.assigned" and "shift" in params:
            params = {"shifts": [params["shift"]]}
        notification.params = _renamed(params)
        notification.save(update_fields=["params"])


class Migration(migrations.Migration):
    dependencies = [("notifications", "0002_notification_kind_notification_params")]

    operations = [migrations.RunPython(unify, migrations.RunPython.noop)]
