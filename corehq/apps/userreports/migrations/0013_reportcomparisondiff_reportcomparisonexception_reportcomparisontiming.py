# Generated by Django 1.11.20 on 2019-05-14 19:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userreports', '0012_datasourceactionlog_skip_destructive'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportComparisonDiff',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('domain', models.TextField()),
                ('control_report_config_id', models.TextField()),
                ('candidate_report_config_id', models.TextField()),
                ('filter_values', models.JSONField()),
                ('control', models.JSONField()),
                ('candidate', models.JSONField()),
                ('diff', models.JSONField()),
            ],
        ),
        migrations.CreateModel(
            name='ReportComparisonException',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('domain', models.TextField()),
                ('control_report_config_id', models.TextField()),
                ('candidate_report_config_id', models.TextField()),
                ('filter_values', models.JSONField()),
                ('exception', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='ReportComparisonTiming',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('domain', models.TextField()),
                ('control_report_config_id', models.TextField()),
                ('candidate_report_config_id', models.TextField()),
                ('filter_values', models.JSONField()),
                ('control_duration', models.DecimalField(decimal_places=3, max_digits=10)),
                ('candidate_duration', models.DecimalField(decimal_places=3, max_digits=10)),
            ],
        ),
    ]
