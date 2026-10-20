from django.conf import settings
from django.db import models


class Liquidacion(models.Model):
    class Tipo(models.TextChoices):
        LABORAL = "laboral", "Laboral"
        CREDITO = "credito", "Crédito"
        CUOTAS = "cuotas", "Cuotas de administración"
        ALIMENTOS = "alimentos", "Alimentos"

    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    referencia = models.CharField(max_length=150, blank=True, help_text="Nombre o asunto de la liquidación")
    expediente = models.ForeignKey(
        "expedientes.Expediente", on_delete=models.SET_NULL, null=True, blank=True, related_name="liquidaciones"
    )
    datos = models.JSONField(help_text="Datos de entrada con los que se calculó")
    resultado = models.JSONField(help_text="Resultado detallado del cálculo")
    total = models.DecimalField(max_digits=16, decimal_places=0)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="liquidaciones"
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Liquidación"
        verbose_name_plural = "Liquidaciones"
        ordering = ["-creado_en"]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.referencia or self.pk}"
