from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='cedula',
            field=models.CharField(blank=True, max_length=12, verbose_name='cédula'),
        ),
        migrations.AddField(
            model_name='usuario',
            name='tarjeta_profesional',
            field=models.CharField(blank=True, max_length=15, verbose_name='tarjeta profesional'),
        ),
    ]
