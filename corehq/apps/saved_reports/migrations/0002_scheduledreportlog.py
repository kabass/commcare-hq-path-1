# Generated by Django 2.2.24 on 2021-09-24 15:45

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('saved_reports', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScheduledReportLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sent_to', models.EmailField(db_index=True, max_length=254)),
                ('domain', models.CharField(db_index=True, max_length=255)),
                ('report_id', models.UUIDField(db_index=True)),
                ('state', models.CharField(max_length=10)),
                ('size', models.PositiveIntegerField()),
                ('timestamp', models.DateTimeField(db_index=True, default=datetime.datetime.utcnow)),
                ('error', models.TextField(null=True)),
            ],
        ),
    ]
