from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('expedientes', '0008_evento_expediente'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AcuerdoPago',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deudor', models.CharField(help_text='Quien se obliga a pagar', max_length=200)),
                ('concepto', models.CharField(max_length=200)),
                ('valor_total', models.DecimalField(decimal_places=2, max_digits=14)),
                ('fecha_acuerdo', models.DateField()),
                ('estado', models.CharField(choices=[('vigente', 'Vigente'), ('cancelado', 'Cancelado')], default='vigente', max_length=20)),
                ('observaciones', models.TextField(blank=True)),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('expediente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='acuerdos_pago', to='expedientes.expediente')),
            ],
            options={
                'verbose_name': 'Acuerdo de pago',
                'verbose_name_plural': 'Acuerdos de pago',
                'ordering': ['-fecha_acuerdo', '-id'],
            },
        ),
        migrations.CreateModel(
            name='CuotaAcuerdo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.PositiveIntegerField()),
                ('valor', models.DecimalField(decimal_places=2, max_digits=14)),
                ('fecha_vencimiento', models.DateField()),
                ('fecha_pago', models.DateField(blank=True, null=True)),
                ('acuerdo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cuotas', to='acuerdos.acuerdopago')),
            ],
            options={
                'verbose_name': 'Cuota de acuerdo',
                'verbose_name_plural': 'Cuotas de acuerdos',
                'ordering': ['numero'],
            },
        ),
    ]
