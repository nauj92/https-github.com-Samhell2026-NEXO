from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expedientes', '0006_juzgado_estructura_rama_judicial'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentoexpediente',
            name='ruta_externa',
            field=models.CharField(blank=True, default='', help_text='Ruta del archivo en el almacenamiento externo', max_length=500),
        ),
        migrations.AlterField(
            model_name='documentoexpediente',
            name='contenido',
            field=models.BinaryField(blank=True, default=b''),
        ),
    ]
