from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords


class Juzgado(models.Model):
    nombre = models.CharField(max_length=200)
    ciudad = models.CharField(max_length=100)
    materia = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.nombre} ({self.ciudad})"

    class Meta:
        verbose_name = "Juzgado"
        verbose_name_plural = "Juzgados"


class Expediente(models.Model):
    class Estado(models.TextChoices):
        ACTIVO = "activo", "Activo"
        TRAMITE = "tramite", "En trámite"
        CERRADO = "cerrado", "Cerrado"

    numero = models.CharField(max_length=30, unique=True)
    juzgado = models.ForeignKey(Juzgado, on_delete=models.PROTECT, related_name="expedientes")
    cliente = models.ForeignKey(
        "clientes.Cliente", on_delete=models.SET_NULL, null=True, blank=True, related_name="expedientes"
    )
    demandante = models.CharField(max_length=200)
    demandado = models.CharField(max_length=200)
    materia = models.CharField(max_length=100)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ACTIVO)
    abogado_asignado = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="expedientes"
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.numero} - {self.demandante} vs. {self.demandado}"

    class Meta:
        verbose_name = "Expediente"
        verbose_name_plural = "Expedientes"
        ordering = ["-creado_en"]


class EtapaProceso(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        EN_CURSO = "en_curso", "En curso"
        COMPLETADA = "completada", "Completada"

    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE, related_name="etapas")
    nombre = models.CharField(max_length=150)
    fecha_limite = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    orden = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.expediente.numero} - {self.nombre}"

    class Meta:
        verbose_name = "Etapa del proceso"
        verbose_name_plural = "Etapas del proceso"
        ordering = ["expediente", "orden"]