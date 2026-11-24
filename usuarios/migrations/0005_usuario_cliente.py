from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0001_initial'),
        ('usuarios', '0004_roles_acoproho'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='cliente',
            field=models.ForeignKey(blank=True, help_text='Solo para usuarios con rol Cliente: ficha del cliente que verá en el portal.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='usuarios_portal', to='clientes.cliente'),
        ),
    ]
