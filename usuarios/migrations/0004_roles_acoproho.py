from django.db import migrations, models


def socios_a_abogados(apps, schema_editor):
    """El antiguo rol «socio_director» pasa a ser un abogado con la marca de socio."""
    Usuario = apps.get_model("usuarios", "Usuario")
    Usuario.objects.filter(rol="socio_director").update(rol="abogado", es_socio=True)


def abogados_socios_a_directores(apps, schema_editor):
    Usuario = apps.get_model("usuarios", "Usuario")
    Usuario.objects.filter(rol="abogado", es_socio=True).update(rol="socio_director")


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0003_primer_ingreso_y_roles'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='es_socio',
            field=models.BooleanField(default=False, help_text='Solo para abogados: ve todos los expedientes.', verbose_name='socio'),
        ),
        migrations.AlterField(
            model_name='usuario',
            name='rol',
            field=models.CharField(choices=[('administrador', 'Administrador'), ('abogado', 'Abogado'), ('secretario_juridico', 'Secretaria'), ('escribiente', 'Escribiente'), ('dependiente', 'Dependiente'), ('cliente', 'Cliente')], default='abogado', max_length=30),
        ),
        migrations.RunPython(socios_a_abogados, abogados_socios_a_directores),
    ]
