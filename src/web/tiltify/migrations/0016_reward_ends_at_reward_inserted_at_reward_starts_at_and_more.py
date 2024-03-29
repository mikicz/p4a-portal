# Generated by Django 4.1.13 on 2024-02-18 11:22

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tiltify", "0015_remove_donation_reward_remove_donation_uuid_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="reward",
            name="ends_at",
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name="reward",
            name="inserted_at",
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name="reward",
            name="starts_at",
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name="reward",
            name="updated_at",
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
    ]
