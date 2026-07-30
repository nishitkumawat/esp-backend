from django.db import migrations, models
import django.db.models.deletion


def migrate_existing_products(apps, schema_editor):
    """Copy single-product data from Invoice into InvoiceItem rows."""
    Invoice = apps.get_model('sells', 'Invoice')
    InvoiceItem = apps.get_model('sells', 'InvoiceItem')

    for invoice in Invoice.objects.all():
        product_name = getattr(invoice, 'product_name', '') or 'Solar Wash Controller'
        quantity = getattr(invoice, 'quantity', 1) or 1
        price_per_unit = getattr(invoice, 'price_per_unit', 0) or 0
        line_total = quantity * price_per_unit

        InvoiceItem.objects.create(
            invoice=invoice,
            product_name=product_name,
            quantity=quantity,
            price_per_unit=price_per_unit,
            line_total=line_total,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('sells', '0004_errorlog'),
    ]

    operations = [
        # 1. Create the InvoiceItem table (while old columns still exist on Invoice)
        migrations.CreateModel(
            name='InvoiceItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invoice', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='items',
                    to='sells.invoice',
                )),
                ('product_name', models.CharField(
                    max_length=200,
                    choices=[
                        ('Solar Wash Controller', 'Solar Wash Controller'),
                        ('Shutter Controller', 'Shutter Controller'),
                        ('Customized Controller', 'Customized Controller'),
                    ],
                )),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('price_per_unit', models.DecimalField(decimal_places=2, max_digits=10)),
                ('line_total', models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=12)),
            ],
            options={
                'verbose_name': 'Invoice Item',
                'verbose_name_plural': 'Invoice Items',
            },
        ),

        # 2. Migrate existing invoice data into InvoiceItem rows
        migrations.RunPython(migrate_existing_products, migrations.RunPython.noop),

        # 3. Change total_amount to be editable with default 0
        migrations.AlterField(
            model_name='invoice',
            name='total_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),

        # 4. Remove old single-product columns from Invoice
        migrations.RemoveField(model_name='invoice', name='product_name'),
        migrations.RemoveField(model_name='invoice', name='quantity'),
        migrations.RemoveField(model_name='invoice', name='price_per_unit'),
    ]
