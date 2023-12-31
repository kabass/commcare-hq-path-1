# Generated by Django 3.2.18 on 2023-06-28 10:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('geospatial', '0001_create_geopolygon'),
    ]

    operations = [
        migrations.CreateModel(
            name='GeoConfig',
            fields=[
                ('domain', models.CharField(db_index=True, max_length=256, primary_key=True, serialize=False)),
                ('location_data_source', models.CharField(default='custom_user_property', max_length=126)),
                ('user_location_property_name', models.CharField(default='commcare_gps_point', max_length=256)),
                ('case_location_property_name', models.CharField(default='commcare_gps_point', max_length=256)),
            ],
        ),
    ]
