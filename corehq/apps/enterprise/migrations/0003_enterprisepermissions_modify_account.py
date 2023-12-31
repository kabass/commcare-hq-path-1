# Generated by Django 2.2.24 on 2021-07-29 21:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('enterprise', '0002_enterprisepermissions_account_unique'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='enterprisepermissions',
                    name='account',
                    field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                                               to='accounting.BillingAccount'),
                ),
            ],
        ),
    ]
