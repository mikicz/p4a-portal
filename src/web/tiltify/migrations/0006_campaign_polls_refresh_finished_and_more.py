# Generated by Django 4.1.5 on 2023-02-04 19:28

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tiltify", "0005_campaign_stream_end_campaign_stream_start"),
    ]

    operations = [
        migrations.AddField(
            model_name="campaign",
            name="polls_refresh_finished",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="campaign",
            name="stats_refresh_finished",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
