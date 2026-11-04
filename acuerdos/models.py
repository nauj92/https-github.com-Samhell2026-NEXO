from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from expedientes.models import Expediente


class AcuerdoPago(models.Model):
    """Acuerdo de pago pactado dentro de un proceso, repartido en cuotas."""

    class Estado(models.TextChoices):
        VIGENTE = "vigente", "Vigente"
        CANCELADO = "cancelado", "Cancelado"

    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE, related_name="acuerdos_pago")
    deudor = models.CharField(max_length=200, help_text="Quien se obliga a pagar")
    concepto = models.CharField(max_length=200)
    valor_total = models.DecimalField(max_digits=14, decimal_places=2)
    fecha_acuerdo = models.DateField()
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.VIGENTE)
    observaciones = models.TextField(blank=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.expediente.numero} - {self.concepto}"

    # Los totales se calculan en Python con las cuotas ya cargadas (prefetch) para no repetir consultas.
    def _cuotas(self):
        return list(self.cuotas.all())

    def total_pagado(self):
        return sum((c.valor for c in self._cuotas() if c.fecha_pago), Decimal("0"))

    def saldo(self):
        return self.valor_total - self.total_pagado()

    def estado_actual(self, hoy=None):
        """cancelado, cumplido (todas las cuotas pagadas), en_mora (alguna vencida sin pagar) o vigente."""
        hoy = hoy or timezone.localdate()
        if self.estado == self.Estado.CANCELADO:
            return "cancelado"
        cuotas = self._cuotas()
        pendientes = [c for c in cuotas if not c.fecha_pago]
        if cuotas and not pendientes:
            return "cumplido"
        if any(c.fecha_vencimiento < hoy for c in pendientes):
            return "en_mora"
        return "vigente"

    class Meta:
        verbose_name = "Acuerdo de pago"
        verbose_name_plural = "Acuerdos de pago"
        ordering = ["-fecha_acuerdo", "-id"]


class CuotaAcuerdo(models.Model):
    acuerdo = models.ForeignKey(AcuerdoPago, on_delete=models.CASCADE, related_name="cuotas")
    numero = models.PositiveIntegerField()
    valor = models.DecimalField(max_digits=14, decimal_places=2)
    fecha_vencimiento = models.DateField()
    fecha_pago = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.acuerdo} - cuota {self.numero}"

    class Meta:
        verbose_name = "Cuota de acuerdo"
        verbose_name_plural = "Cuotas de acuerdos"
        ordering = ["numero"]
