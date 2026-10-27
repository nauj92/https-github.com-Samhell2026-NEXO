from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demandas', '0002_borrador_contestacion_citacion'),
    ]

    operations = [
        migrations.AddField(
            model_name='demanda',
            name='juez_destinatario',
            field=models.CharField(blank=True, help_text='Ej.: Juez Civil del Circuito de Cali (Reparto)', max_length=200),
        ),
        migrations.AddField(
            model_name='demanda',
            name='demandante_tipo_persona',
            field=models.CharField(choices=[('natural', 'Persona natural'), ('juridica', 'Persona jurídica o patrimonio autónomo')], default='natural', max_length=10),
        ),
        migrations.AddField(
            model_name='demanda',
            name='demandante_tipo_documento',
            field=models.CharField(blank=True, choices=[('CC', 'Cédula de ciudadanía'), ('CE', 'Cédula de extranjería'), ('NIT', 'NIT'), ('PAS', 'Pasaporte')], max_length=3),
        ),
        migrations.AddField(
            model_name='demanda',
            name='demandante_documento',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='demanda',
            name='demandante_domicilio',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='demanda',
            name='demandante_representante',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='demanda',
            name='demandante_representante_documento',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='demanda',
            name='demandado_tipo_persona',
            field=models.CharField(choices=[('natural', 'Persona natural'), ('juridica', 'Persona jurídica o patrimonio autónomo')], default='natural', max_length=10),
        ),
        migrations.AddField(
            model_name='demanda',
            name='demandado_tipo_documento',
            field=models.CharField(blank=True, choices=[('CC', 'Cédula de ciudadanía'), ('CE', 'Cédula de extranjería'), ('NIT', 'NIT'), ('PAS', 'Pasaporte')], max_length=3),
        ),
        migrations.AddField(
            model_name='demanda',
            name='demandado_documento',
            field=models.CharField(blank=True, help_text='Si se conoce', max_length=30),
        ),
        migrations.AddField(
            model_name='demanda',
            name='demandado_domicilio',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='demanda',
            name='demandado_representante',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='demanda',
            name='demandado_ubicacion_desconocida',
            field=models.BooleanField(default=False, help_text='Se desconoce el domicilio del demandado o el lugar de notificación (parágrafo 1)'),
        ),
        migrations.AddField(
            model_name='demanda',
            name='otras_partes',
            field=models.TextField(blank=True, help_text='Otros demandantes o demandados, con sus datos'),
        ),
        migrations.AddField(
            model_name='demanda',
            name='sin_apoderado',
            field=models.BooleanField(default=False, help_text='El demandante actúa sin apoderado judicial'),
        ),
        migrations.AddField(
            model_name='demanda',
            name='apoderado_nombre',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='demanda',
            name='apoderado_documento',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='demanda',
            name='apoderado_tarjeta_profesional',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='demanda',
            name='hechos',
            field=models.JSONField(blank=True, default=list, help_text='Lista de hechos; se numeran en el escrito'),
        ),
        migrations.AddField(
            model_name='demanda',
            name='pruebas',
            field=models.TextField(blank=True, help_text='Pruebas que se pretende hacer valer'),
        ),
        migrations.AddField(
            model_name='demanda',
            name='documentos_en_poder_demandado',
            field=models.TextField(blank=True, help_text='Documentos que el demandado tiene en su poder, para que los aporte'),
        ),
        migrations.AddField(
            model_name='demanda',
            name='requiere_juramento_estimatorio',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='demanda',
            name='juramento_estimatorio',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='demanda',
            name='fundamentos_derecho',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='demanda',
            name='cuantia_aplica',
            field=models.BooleanField(default=True, help_text='La cuantía es necesaria para determinar competencia o trámite'),
        ),
        migrations.AddField(
            model_name='demanda',
            name='notif_demandante_direccion',
            field=models.CharField(blank=True, max_length=250),
        ),
        migrations.AddField(
            model_name='demanda',
            name='notif_demandante_email',
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name='demanda',
            name='notif_demandado_direccion',
            field=models.CharField(blank=True, max_length=250),
        ),
        migrations.AddField(
            model_name='demanda',
            name='notif_demandado_email',
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name='demanda',
            name='notif_apoderado_direccion',
            field=models.CharField(blank=True, max_length=250),
        ),
        migrations.AddField(
            model_name='demanda',
            name='notif_apoderado_email',
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name='demanda',
            name='otros_requisitos',
            field=models.TextField(blank=True, help_text='Conciliación prejudicial, anexos, medidas cautelares y demás exigidos por la ley'),
        ),
    ]
