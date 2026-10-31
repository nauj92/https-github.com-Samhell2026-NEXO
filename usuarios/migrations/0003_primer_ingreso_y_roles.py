from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0002_cedula_tarjeta_profesional'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuario',
            name='rol',
            field=models.CharField(choices=[('administrador', 'Administrador'), ('socio_director', 'Socio Director'), ('abogado', 'Abogado'), ('secretario_juridico', 'Secretario(a) Jurídico'), ('escribiente', 'Escribiente'), ('cliente', 'Cliente')], default='abogado', max_length=30),
        ),
        migrations.AddField(
            model_name='usuario',
            name='debe_cambiar_password',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='usuario',
            name='autorizacion_datos_pendiente',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='usuario',
            name='fecha_autorizacion_datos',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
