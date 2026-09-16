from __future__ import annotations

from django.db import migrations


def create_manager_position(apps, schema_editor):
    Position = apps.get_model("accounts", "Position")
    Position.objects.get_or_create(name="Manager")


class Migration(migrations.Migration):
    """Seeds the permanent "Manager" position (see `accounts.models.MANAGER_POSITION_NAME`)."""

    dependencies = [
        ("accounts", "0006_position_alter_user_position"),
    ]

    operations = [
        migrations.RunPython(create_manager_position, migrations.RunPython.noop),
    ]
