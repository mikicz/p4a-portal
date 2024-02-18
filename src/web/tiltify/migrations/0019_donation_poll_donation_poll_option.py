# Generated by Django 4.1.13 on 2024-02-18 11:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tiltify", "0018_poll_option"),
    ]

    operations = [
        migrations.AddField(
            model_name="donation",
            name="poll",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="tiltify.poll"
            ),
        ),
        migrations.AddField(
            model_name="donation",
            name="poll_option",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="tiltify.option"
            ),
        ),
    ]
