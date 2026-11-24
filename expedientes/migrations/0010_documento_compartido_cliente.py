from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expedientes', '0009_expediente_colaboradores'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentoexpediente',
            name='compartido_cliente',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='documentoexpediente',
            name='origen_cliente',
            field=models.BooleanField(default=False),
        ),
    ]
