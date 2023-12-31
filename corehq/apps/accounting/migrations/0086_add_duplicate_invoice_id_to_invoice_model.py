# Generated by Django 3.2.20 on 2023-09-14 01:13

from django.db import migrations, models
from django.db.models import Count, Q


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0085_remove_free_50_sms'),
    ]

    def _populate_duplicate_invoice_id(apps, schema_editor):
        Invoice = apps.get_model('accounting', 'Invoice')
        duplicates = (Invoice.objects.filter(is_hidden_to_ops=False)
            .values('subscription', 'date_start', 'date_end')
            .annotate(count=Count('id'))
            .filter(count__gt=1))
        for duplicate in duplicates:
            duplicate_invoices = Invoice.objects.filter(subscription=duplicate['subscription'],
                                                        date_start=duplicate['date_start'],
                                                        date_end=duplicate['date_end']).order_by('date_created')
            first_invoice = duplicate_invoices.first()
            duplicate_invoices.filter(
                ~Q(id=first_invoice.id)
            ).update(duplicate_invoice_id=first_invoice.id)

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='duplicate_invoice_id',
            field=models.IntegerField(null=True),
        ),
        migrations.RunPython(_populate_duplicate_invoice_id, reverse_code=migrations.RunPython.noop),
    ]
