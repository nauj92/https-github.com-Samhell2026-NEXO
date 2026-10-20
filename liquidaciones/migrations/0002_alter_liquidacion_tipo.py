from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('liquidaciones', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='liquidacion',
            name='tipo',
            field=models.CharField(choices=[('laboral', 'Laboral'), ('credito', 'Crédito'), ('cuotas', 'Cuotas de administración'), ('alimentos', 'Alimentos')], max_length=20),
        ),
    ]
