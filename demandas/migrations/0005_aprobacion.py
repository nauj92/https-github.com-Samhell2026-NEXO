from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

APROBACION = [('borrador', 'Borrador'), ('pendiente', 'Pendiente de aprobación'), ('aprobado', 'Aprobado'), ('devuelto', 'Devuelto para ajustes')]


class Migration(migrations.Migration):
    # Los escritos que ya existían quedan «aprobados» (el AddField los crea con ese valor);
    # los nuevos nacen como borrador (AlterField).

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('demandas', '0004_requisitos_articulo_96'),
    ]

    operations = [
        migrations.AddField(
            model_name='demanda',
            name='aprobacion',
            field=models.CharField(choices=APROBACION, default='aprobado', max_length=12),
        ),
        migrations.AlterField(
            model_name='demanda',
            name='aprobacion',
            field=models.CharField(choices=APROBACION, default='borrador', max_length=12),
        ),
        migrations.AddField(
            model_name='demanda',
            name='enviado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='demanda',
            name='aprobado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='demanda',
            name='aprobado_en',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='demanda',
            name='motivo_devolucion',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='aprobacion',
            field=models.CharField(choices=APROBACION, default='aprobado', max_length=12),
        ),
        migrations.AlterField(
            model_name='contestaciondemanda',
            name='aprobacion',
            field=models.CharField(choices=APROBACION, default='borrador', max_length=12),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='enviado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='aprobado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='aprobado_en',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='motivo_devolucion',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='citacion',
            name='aprobacion',
            field=models.CharField(choices=APROBACION, default='aprobado', max_length=12),
        ),
        migrations.AlterField(
            model_name='citacion',
            name='aprobacion',
            field=models.CharField(choices=APROBACION, default='borrador', max_length=12),
        ),
        migrations.AddField(
            model_name='citacion',
            name='enviado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='citacion',
            name='aprobado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='citacion',
            name='aprobado_en',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='citacion',
            name='motivo_devolucion',
            field=models.TextField(blank=True),
        ),
    ]
