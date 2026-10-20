import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expedientes', '0004_expediente_cliente_historicalexpediente_cliente'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentoExpediente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255)),
                ('tipo_contenido', models.CharField(blank=True, max_length=100)),
                ('tamano', models.PositiveIntegerField()),
                ('contenido', models.BinaryField()),
                ('subido_en', models.DateTimeField(auto_now_add=True)),
                ('expediente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documentos', to='expedientes.expediente')),
                ('subido_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='documentos_subidos', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Documento del expediente',
                'verbose_name_plural': 'Documentos del expediente',
                'ordering': ['-subido_en'],
            },
        ),
    ]
