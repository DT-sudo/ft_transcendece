from __future__ import annotations

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """Completes the Position move started in accounts.0006: shifts now point at
    accounts.Position, and scheduling's own (now tableless) Position model is dropped
    from the migration state only - its table was already renamed away."""

    dependencies = [
        ('accounts', '0006_position_alter_user_position'),
        ('scheduling', '0004_shift_version'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shift',
            name='position',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='shifts', to='accounts.position'),
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(name='Position'),
            ],
        ),
    ]
