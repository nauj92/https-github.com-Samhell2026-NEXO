from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('expedientes', '0009_expediente_colaboradores'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Tarea',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=200)),
                ('descripcion', models.TextField(blank=True)),
                ('tipo', models.CharField(choices=[('presentar_escrito', 'Presentar escrito'), ('retirar_copias', 'Retirar copias'), ('notificar', 'Notificar'), ('diligencia', 'Diligencia'), ('redactar', 'Redactar borrador'), ('otra', 'Otra')], default='otra', max_length=20)),
                ('fecha_limite', models.DateField(blank=True, null=True)),
                ('estado', models.CharField(choices=[('pendiente', 'Pendiente'), ('en_curso', 'En curso'), ('realizada', 'Realizada')], default='pendiente', max_length=20)),
                ('fecha_realizada', models.DateTimeField(blank=True, null=True)),
                ('observacion_cierre', models.TextField(blank=True, help_text='Lo que encontró o resolvió quien hizo el trámite')),
                ('creada_en', models.DateTimeField(auto_now_add=True)),
                ('actualizada_en', models.DateTimeField(auto_now=True)),
                ('asignado_a', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tareas_asignadas', to=settings.AUTH_USER_MODEL)),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('expediente', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tareas', to='expedientes.expediente')),
            ],
            options={
                'verbose_name': 'Tarea',
                'verbose_name_plural': 'Tareas',
                'ordering': ['-creada_en'],
            },
        ),
        migrations.CreateModel(
            name='ComprobanteTarea',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255)),
                ('tipo_contenido', models.CharField(blank=True, max_length=100)),
                ('tamano', models.PositiveIntegerField()),
                ('contenido', models.BinaryField(blank=True, default=b'')),
                ('ruta_externa', models.CharField(blank=True, default='', max_length=500)),
                ('subido_en', models.DateTimeField(auto_now_add=True)),
                ('subido_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('tarea', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comprobantes', to='tareas.tarea')),
            ],
            options={
                'verbose_name': 'Comprobante de tarea',
                'verbose_name_plural': 'Comprobantes de tareas',
                'ordering': ['-subido_en'],
            },
        ),
    ]
