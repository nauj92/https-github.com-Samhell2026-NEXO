from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('audiencias', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='audiencia',
            name='tipo',
            field=models.CharField(choices=[('audiencia', 'Audiencia'), ('diligencia', 'Diligencia judicial')], default='audiencia', max_length=20),
        ),
        migrations.AddField(
            model_name='audiencia',
            name='clase',
            field=models.CharField(blank=True, help_text='Ej.: inicial, de instrucción y juzgamiento, inspección judicial, secuestro, remate', max_length=100),
        ),
        migrations.AlterModelOptions(
            name='audiencia',
            options={'ordering': ['fecha_hora'], 'verbose_name': 'Audiencia o diligencia', 'verbose_name_plural': 'Audiencias y diligencias'},
        ),
    ]
