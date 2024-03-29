# Generated by Django 4.1.13 on 2024-02-13 21:00

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tiltify", "0014_alter_donation_uuid"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="donation",
            name="reward",
        ),
        migrations.RemoveField(
            model_name="donation",
            name="id",
        ),
        migrations.RenameField(model_name="donation", old_name="uuid", new_name="id"),
        migrations.AlterField(
            model_name="donation",
            name="id",
            field=models.UUIDField(primary_key=True, serialize=False),
        ),
        migrations.CreateModel(
            name="RewardClaim",
            fields=[
                ("id", models.UUIDField(primary_key=True, serialize=False)),
                ("quantity", models.IntegerField()),
                (
                    "donation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="tiltify.donation",
                    ),
                ),
                (
                    "reward",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tiltify.reward"),
                ),
            ],
        ),
    ]
