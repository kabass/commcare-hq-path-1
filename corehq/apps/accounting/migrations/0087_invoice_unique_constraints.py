# Generated by Django 3.2.20 on 2023-08-25 15:38

from django.db import migrations, models

# Raw SQL to add unique constraints to Invoice model
INVOICE_TABLE_INDEX_NAME = 'unique_invoice_per_subscription_period'
INVOICE_TABLE_COLUMNS = ['subscription_id', 'date_start', 'date_end']
CREATE_INVOICE_INDEX_SQL = (f"CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS {INVOICE_TABLE_INDEX_NAME} ON accounting_invoice ({','.join(INVOICE_TABLE_COLUMNS)}) "
"WHERE is_hidden_to_ops = False AND duplicate_invoice_id IS NULL")
DROP_INVOICE_INDEX_SQL = f"DROP INDEX CONCURRENTLY IF EXISTS {INVOICE_TABLE_INDEX_NAME}"

# Raw SQL to add unique constraints to Customer Invoice model
CUSTOMER_INVOICE_TABLE_INDEX_NAME = 'unique_customer_invoice_per_subscription_period'
CUSTOMER_INVOICE_TABLE_COLUMNS = ['account_id', 'date_start', 'date_end']
CREATE_CUSTOMER_INVOICE_INDEX_SQL = f"CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS {CUSTOMER_INVOICE_TABLE_INDEX_NAME} ON accounting_customerinvoice ({','.join(CUSTOMER_INVOICE_TABLE_COLUMNS)}) WHERE is_hidden_to_ops = False"
DROP_CUSTOMER_INVOICE_INDEX_SQL = f"DROP INDEX CONCURRENTLY IF EXISTS {CUSTOMER_INVOICE_TABLE_INDEX_NAME}"


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('accounting', '0086_add_duplicate_invoice_id_to_invoice_model'),
    ]

    operations = [
        migrations.RunSQL(
            sql=CREATE_INVOICE_INDEX_SQL,
            reverse_sql=DROP_INVOICE_INDEX_SQL,
            state_operations=[
                migrations.AddConstraint(
                    model_name='invoice',
                    constraint=models.UniqueConstraint(condition=models.Q(('is_hidden_to_ops', False), ('duplicate_invoice_id__isnull', True)), fields=('subscription', 'date_start', 'date_end'), name=INVOICE_TABLE_INDEX_NAME),
                )
            ]
        ),
        migrations.RunSQL(
            sql=CREATE_CUSTOMER_INVOICE_INDEX_SQL,
            reverse_sql=DROP_CUSTOMER_INVOICE_INDEX_SQL,
            state_operations=[
                migrations.AddConstraint(
                    model_name='customerinvoice',
                    constraint=models.UniqueConstraint(condition=models.Q(('is_hidden_to_ops', False)), fields=('account', 'date_start', 'date_end'), name=CUSTOMER_INVOICE_TABLE_INDEX_NAME),
                )
            ]
        )
    ]
