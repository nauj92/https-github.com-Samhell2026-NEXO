from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notificaciones', '0002_notificacion_clave'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notificacion',
            name='tipo',
            field=models.CharField(choices=[('audiencia', 'Audiencia próxima'), ('plazo', 'Plazo procesal'), ('factura', 'Factura'), ('tarea', 'Tarea'), ('borrador', 'Borrador pendiente'), ('general', 'General')], default='general', max_length=20),
        ),
    ]
