from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('facturacion', '0003_factura_cliente'),
    ]

    operations = [
        migrations.AddField(
            model_name='factura',
            name='fecha_pago',
            field=models.DateField(blank=True, null=True),
        ),
    ]
