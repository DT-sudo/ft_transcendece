import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def copy_position_names(apps, schema_editor):
    Shift = apps.get_model("scheduling", "Shift")
    for shift in Shift.objects.select_related("position").iterator():
        shift.position_name = shift.position.name
        shift.save(update_fields=["position_name"])


class Migration(migrations.Migration):
    """Deleting a position keeps its worked shifts under the name they were worked under,
    and deleting a manager keeps the shifts they wrote: the schedule is shared."""

    dependencies = [
        ("accounts", "0007_manager_position"),
        ("scheduling", "0005_alter_shift_position_delete_position"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="shift",
            name="position_name",
            field=models.CharField(default="", editable=False, max_length=25),
            preserve_default=False,
        ),
        migrations.RunPython(copy_position_names, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="shift",
            name="position",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="shifts", to="accounts.position"
            ),
        ),
        migrations.AlterField(
            model_name="shift",
            name="created_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_shifts",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
