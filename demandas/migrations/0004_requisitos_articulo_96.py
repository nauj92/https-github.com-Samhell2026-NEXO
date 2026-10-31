import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demandas', '0003_requisitos_articulo_82'),
    ]

    operations = [
        migrations.AddField(
            model_name='contestaciondemanda',
            name='demanda',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contestaciones', to='demandas.demanda'),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='demandado_tipo_persona',
            field=models.CharField(choices=[('natural', 'Persona natural'), ('juridica', 'Persona jurídica o patrimonio autónomo')], default='natural', max_length=10),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='demandado_tipo_documento',
            field=models.CharField(blank=True, choices=[('CC', 'Cédula de ciudadanía'), ('CE', 'Cédula de extranjería'), ('NIT', 'NIT'), ('PAS', 'Pasaporte')], max_length=3),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='demandado_documento',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='demandado_domicilio',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='demandado_representante',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='demandado_representante_documento',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='sin_apoderado',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='apoderado_nombre',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='apoderado_documento',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='apoderado_tarjeta_profesional',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='apoderado_domicilio',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='pronunciamiento_pretensiones',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='pronunciamientos_hechos',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='excepciones_merito',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='sin_excepciones',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='objeta_juramento_estimatorio',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='objecion_juramento',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='alega_derecho_retencion',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='derecho_retencion',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='pruebas_en_expediente',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='notif_demandado_direccion',
            field=models.CharField(blank=True, max_length=250),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='notif_demandado_email',
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='notif_apoderado_direccion',
            field=models.CharField(blank=True, max_length=250),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='notif_apoderado_email',
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='anexo_poder',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='anexo_existencia_representacion',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='documentos_solicitados',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='contestaciondemanda',
            name='anexos_otros',
            field=models.TextField(blank=True),
        ),
    ]
