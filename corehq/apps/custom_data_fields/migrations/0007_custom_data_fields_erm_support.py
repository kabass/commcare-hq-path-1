# Generated by Django 3.2.15 on 2022-10-11 19:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_data_fields', '0006_auto_20200924_1753'),
    ]

    operations = [
        migrations.AddField(
            model_name='customdatafieldsprofile',
            name='is_synced',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='field',
            name='is_synced',
            field=models.BooleanField(default=False),
        ),
    ]
