import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('expedientes', '0005_documentoexpediente'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Liquidacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('laboral', 'Laboral'), ('credito', 'Crédito'), ('cuotas', 'Cuotas de administración')], max_length=20)),
                ('referencia', models.CharField(blank=True, help_text='Nombre o asunto de la liquidación', max_length=150)),
                ('datos', models.JSONField(help_text='Datos de entrada con los que se calculó')),
                ('resultado', models.JSONField(help_text='Resultado detallado del cálculo')),
                ('total', models.DecimalField(decimal_places=0, max_digits=16)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='liquidaciones', to=settings.AUTH_USER_MODEL)),
                ('expediente', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='liquidaciones', to='expedientes.expediente')),
            ],
            options={
                'verbose_name': 'Liquidación',
                'verbose_name_plural': 'Liquidaciones',
                'ordering': ['-creado_en'],
            },
        ),
    ]
