# Generated by Django 4.1.5 on 2023-01-09 20:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Campaign",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ],
        ),
        migrations.CreateModel(
            name="Reward",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=20)),
            ],
        ),
        migrations.CreateModel(
            name="Poll",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("active", models.BooleanField()),
                ("created_at", models.DateTimeField()),
                ("updated_at", models.DateTimeField()),
                ("campaign", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tiltify.campaign")),
            ],
        ),
        migrations.CreateModel(
            name="Option",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("total_amount_raised", models.DecimalField(decimal_places=2, max_digits=20)),
                ("created_at", models.DateTimeField()),
                ("updated_at", models.DateTimeField()),
                ("poll", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tiltify.poll")),
            ],
        ),
        migrations.CreateModel(
            name="Donation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=20)),
                ("name", models.CharField(max_length=255)),
                ("comment", models.CharField(blank=True, max_length=255, null=True)),
                ("completed_at", models.DateTimeField()),
                ("campaign", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tiltify.campaign")),
                (
                    "reward",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="tiltify.reward"
                    ),
                ),
            ],
        ),
    ]
