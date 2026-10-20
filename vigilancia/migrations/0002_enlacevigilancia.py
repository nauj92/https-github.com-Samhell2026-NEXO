import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vigilancia', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EnlaceVigilancia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=150)),
                ('url', models.URLField(max_length=1000)),
                ('nota', models.CharField(blank=True, max_length=300)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='enlaces_vigilancia', to=settings.AUTH_USER_MODEL)),
                ('vigilancia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enlaces', to='vigilancia.vigilancia')),
            ],
            options={
                'verbose_name': 'Enlace anclado',
                'verbose_name_plural': 'Enlaces anclados',
                'ordering': ['-creado_en'],
            },
        ),
    ]
