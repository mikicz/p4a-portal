# Generated by Django 4.1.5 on 2023-02-04 19:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tiltify", "0006_campaign_polls_refresh_finished_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="campaign",
            name="keep_refreshing",
            field=models.BooleanField(default=True),
        ),
    ]
