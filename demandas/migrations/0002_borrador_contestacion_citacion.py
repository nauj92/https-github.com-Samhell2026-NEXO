import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0001_initial'),
        ('demandas', '0001_initial'),
        ('expedientes', '0005_documentoexpediente'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='demanda',
            name='borrador',
            field=models.TextField(blank=True, help_text='Borrador del escrito de demanda (editable)'),
        ),
        migrations.CreateModel(
            name='ContestacionDemanda',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('clase_proceso', models.CharField(max_length=150)),
                ('demandante', models.CharField(max_length=200)),
                ('demandado', models.CharField(help_text='Normalmente el cliente del despacho', max_length=200)),
                ('fecha_notificacion', models.DateField(blank=True, help_text='Cuando quedó notificada la demanda', null=True)),
                ('dias_termino', models.PositiveSmallIntegerField(default=20, help_text='Días hábiles de traslado')),
                ('estado', models.CharField(choices=[('por_elaborar', 'Por elaborar'), ('en_elaboracion', 'En elaboración'), ('presentada', 'Presentada'), ('no_contestada', 'No contestada')], default='por_elaborar', max_length=20)),
                ('fecha_presentacion', models.DateField(blank=True, null=True)),
                ('excepciones', models.TextField(blank=True, help_text='Excepciones de mérito y previas')),
                ('pruebas', models.TextField(blank=True)),
                ('borrador', models.TextField(blank=True)),
                ('observaciones', models.TextField(blank=True)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('actualizado_en', models.DateTimeField(auto_now=True)),
                ('abogado_responsable', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contestaciones', to=settings.AUTH_USER_MODEL)),
                ('cliente', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contestaciones', to='clientes.cliente')),
                ('expediente', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contestaciones', to='expedientes.expediente')),
                ('juzgado', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contestaciones', to='expedientes.juzgado')),
            ],
            options={
                'verbose_name': 'Contestación de demanda',
                'verbose_name_plural': 'Contestaciones de demanda',
                'ordering': ['-creado_en'],
            },
        ),
        migrations.CreateModel(
            name='Citacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('destinatario', models.CharField(max_length=200)),
                ('direccion', models.CharField(blank=True, max_length=250)),
                ('tipo', models.CharField(choices=[('citacion', 'Citación para notificación personal (art. 291)'), ('aviso', 'Notificación por aviso (art. 292)')], default='citacion', max_length=20)),
                ('ubicacion', models.CharField(choices=[('mismo_municipio', 'Mismo municipio del juzgado'), ('otro_municipio', 'Otro municipio del país'), ('exterior', 'En el exterior')], default='mismo_municipio', max_length=20)),
                ('estado', models.CharField(choices=[('pendiente', 'Pendiente de envío'), ('enviada', 'Enviada'), ('entregada', 'Entregada'), ('devuelta', 'Devuelta (no entregada)'), ('notificado', 'Notificado')], default='pendiente', max_length=20)),
                ('fecha_envio', models.DateField(blank=True, null=True)),
                ('empresa_mensajeria', models.CharField(blank=True, max_length=100)),
                ('guia', models.CharField(blank=True, max_length=60)),
                ('fecha_entrega', models.DateField(blank=True, null=True)),
                ('fecha_notificacion', models.DateField(blank=True, help_text='Cuando el demandado se notificó personalmente', null=True)),
                ('observaciones', models.TextField(blank=True)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('actualizado_en', models.DateTimeField(auto_now=True)),
                ('abogado_responsable', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='citaciones', to=settings.AUTH_USER_MODEL)),
                ('demanda', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='citaciones', to='demandas.demanda')),
                ('expediente', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='citaciones', to='expedientes.expediente')),
            ],
            options={
                'verbose_name': 'Citación',
                'verbose_name_plural': 'Citaciones',
                'ordering': ['-creado_en'],
            },
        ),
    ]
