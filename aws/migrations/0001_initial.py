# Generated by Django 4.1.2 on 2022-10-15 22:23

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="EC2Instances",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_date", models.DateTimeField()),
                ("instance_id", models.CharField(max_length=200, unique=True)),
                ("instance_type", models.CharField(max_length=200)),
                ("key_name", models.CharField(max_length=200)),
                ("internal_ip", models.CharField(max_length=200)),
                ("external_ip", models.CharField(max_length=200)),
            ],
        ),
    ]