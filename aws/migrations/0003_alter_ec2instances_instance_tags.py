# Generated by Django 4.1.2 on 2022-10-15 23:02

from django.db import migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ("aws", "0002_ec2instances_instance_name_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ec2instances",
            name="instance_tags",
            field=jsonfield.fields.JSONField(default={}),
        ),
    ]
