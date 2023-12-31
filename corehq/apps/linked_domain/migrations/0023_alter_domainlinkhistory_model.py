# Generated by Django 3.2.19 on 2023-06-15 08:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('linked_domain', '0022_alter_domainlinkhistory_model'),
    ]

    operations = [
        migrations.AlterField(
            model_name='domainlinkhistory',
            name='model',
            field=models.CharField(choices=[('app', 'Application'), ('fixture', 'Lookup Table'), ('report', 'Report'), ('keyword', 'Keyword'), ('ucr_expression', 'Data Expressions and Filters'), ('custom_user_data', 'Custom User Data Fields'), ('custom_location_data', 'Custom Location Data Fields'), ('roles', 'User Roles'), ('previews', 'Feature Previews'), ('auto_update_rules', 'Automatic Update Rules'), ('data_dictionary', 'Data Dictionary'), ('case_search_data', 'Case Search Settings'), ('dialer_settings', 'Dialer Settings'), ('otp_settings', 'OTP Pass-through Settings'), ('hmac_callout_settings', 'Signed Callout'), ('tableau_server_and_visualizations', 'Tableau Server and Visualizations'), ('custom_product_data', 'Custom Product Data Fields'), ('toggles', 'Feature Flags')], max_length=128),
        ),
    ]
