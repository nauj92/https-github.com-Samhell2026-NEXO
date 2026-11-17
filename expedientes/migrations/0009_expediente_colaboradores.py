from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expedientes', '0008_evento_expediente'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='expediente',
            name='colaboradores',
            field=models.ManyToManyField(blank=True, help_text='Secretarias y escribientes que ven este expediente.', related_name='expedientes_apoyo', to=settings.AUTH_USER_MODEL),
        ),
    ]
