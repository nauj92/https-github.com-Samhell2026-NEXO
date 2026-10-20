from django.db import models
from expedientes.models import Expediente


class Audiencia(models.Model):
    class Tipo(models.TextChoices):
        AUDIENCIA = "audiencia", "Audiencia"
        DILIGENCIA = "diligencia", "Diligencia judicial"

    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.AUDIENCIA)
    clase = models.CharField(max_length=100, blank=True, help_text="Ej.: inicial, de instrucción y juzgamiento, inspección judicial, secuestro, remate")
    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE, related_name="audiencias")
    fecha_hora = models.DateTimeField()
    lugar = models.CharField(max_length=200)
    observaciones = models.TextField(blank=True)

    def __str__(self):
        return f"{self.expediente.numero} - {self.fecha_hora:%d/%m/%Y %H:%M}"

    class Meta:
        verbose_name = "Audiencia o diligencia"
        verbose_name_plural = "Audiencias y diligencias"
        ordering = ["fecha_hora"]