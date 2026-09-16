from __future__ import annotations

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """Moves Position from the scheduling app to accounts, which owns the Users page.

    The table is renamed in place, so existing rows and the ids `User.position` and
    `Shift.position` point at survive untouched; only the migration state (which app
    owns the model) and the two foreign keys' target change.
    """

    dependencies = [
        ('accounts', '0005_user_language'),
        ('scheduling', '0004_shift_version'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql='ALTER TABLE "scheduling_position" RENAME TO "accounts_position";',
                    reverse_sql='ALTER TABLE "accounts_position" RENAME TO "scheduling_position";',
                ),
            ],
            state_operations=[
                migrations.CreateModel(
                    name='Position',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('name', models.CharField(max_length=25, unique=True)),
                    ],
                ),
            ],
        ),
        migrations.AlterField(
            model_name='user',
            name='position',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='employees', to='accounts.position'),
        ),
    ]
