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
            name='Vigilancia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activa', models.BooleanField(default=True)),
                ('dias_alerta', models.PositiveSmallIntegerField(default=30, help_text='Días sin movimiento tras los cuales se genera una alerta')),
                ('observaciones', models.TextField(blank=True)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='vigilancias_creadas', to=settings.AUTH_USER_MODEL)),
                ('expediente', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='vigilancia', to='expedientes.expediente')),
            ],
            options={
                'verbose_name': 'Vigilancia judicial',
                'verbose_name_plural': 'Vigilancias judiciales',
                'ordering': ['-creado_en'],
            },
        ),
        migrations.CreateModel(
            name='ActuacionVigilancia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField()),
                ('descripcion', models.CharField(max_length=500)),
                ('registrada_en', models.DateTimeField(auto_now_add=True)),
                ('registrada_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='actuaciones_registradas', to=settings.AUTH_USER_MODEL)),
                ('vigilancia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actuaciones', to='vigilancia.vigilancia')),
            ],
            options={
                'verbose_name': 'Actuación',
                'verbose_name_plural': 'Actuaciones',
                'ordering': ['-fecha', '-id'],
            },
        ),
    ]
