import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('clientes', '0001_initial'),
        ('expedientes', '0005_documentoexpediente'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Demanda',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('clase_proceso', models.CharField(help_text='Ej.: Ejecutivo singular, Ordinario laboral', max_length=150)),
                ('demandante', models.CharField(max_length=200)),
                ('demandado', models.CharField(max_length=200)),
                ('pretensiones', models.TextField()),
                ('cuantia', models.DecimalField(decimal_places=2, default=0, max_digits=16)),
                ('estado', models.CharField(choices=[('elaboracion', 'En elaboración'), ('radicada', 'Radicada'), ('inadmitida', 'Inadmitida (subsanar)'), ('admitida', 'Admitida'), ('rechazada', 'Rechazada'), ('retirada', 'Retirada')], default='elaboracion', max_length=20)),
                ('fecha_radicacion', models.DateField(blank=True, null=True)),
                ('fecha_inadmision', models.DateField(blank=True, null=True)),
                ('fecha_admision', models.DateField(blank=True, null=True)),
                ('observaciones', models.TextField(blank=True)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('actualizado_en', models.DateTimeField(auto_now=True)),
                ('abogado_responsable', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='demandas', to=settings.AUTH_USER_MODEL)),
                ('cliente', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='demandas', to='clientes.cliente')),
                ('expediente', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='demandas', to='expedientes.expediente')),
                ('juzgado', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='demandas', to='expedientes.juzgado')),
            ],
            options={
                'verbose_name': 'Demanda',
                'verbose_name_plural': 'Demandas',
                'ordering': ['-creado_en'],
            },
        ),
    ]
