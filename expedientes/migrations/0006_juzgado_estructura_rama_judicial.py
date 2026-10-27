from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("expedientes", "0005_documentoexpediente"),
    ]

    operations = [
        migrations.AddField(
            model_name="juzgado",
            name="codigo",
            field=models.CharField(
                blank=True, help_text="Código de 12 dígitos de la Rama Judicial (p. ej. 110013109032).",
                max_length=12, null=True, unique=True, verbose_name="código del despacho",
            ),
        ),
        migrations.AddField(
            model_name="juzgado",
            name="departamento",
            field=models.CharField(blank=True, default="", max_length=60),
        ),
        migrations.AddField(
            model_name="juzgado",
            name="municipio",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="juzgado",
            name="entidad",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
        migrations.AddField(
            model_name="juzgado",
            name="especialidad",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
        migrations.AlterField(
            model_name="juzgado",
            name="ciudad",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AlterField(
            model_name="juzgado",
            name="materia",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
    ]
