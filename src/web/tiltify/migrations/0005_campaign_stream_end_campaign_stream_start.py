# Generated by Django 4.1.5 on 2023-01-17 21:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tiltify", "0004_alter_donation_comment"),
    ]

    operations = [
        migrations.AddField(
            model_name="campaign",
            name="stream_end",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="campaign",
            name="stream_start",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]