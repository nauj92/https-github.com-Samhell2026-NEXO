from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('expedientes', '0007_documento_almacenamiento_externo'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EventoExpediente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(max_length=60)),
                ('cambios', models.JSONField(blank=True, default=list, help_text='Lista de {campo, anterior, nuevo}')),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('expediente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eventos', to='expedientes.expediente')),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Evento del expediente',
                'verbose_name_plural': 'Eventos del expediente',
                'ordering': ['-fecha', '-id'],
            },
        ),
    ]
