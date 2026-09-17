from django.db import models
from expedientes.models import Expediente


class Factura(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        PAGADA = "pagada", "Pagada"
        VENCIDA = "vencida", "Vencida"
        ANULADA = "anulada", "Anulada"

    numero = models.CharField(max_length=30, unique=True)
    expediente = models.ForeignKey(
        Expediente, on_delete=models.PROTECT, related_name="facturas", null=True, blank=True
    )
    cliente = models.ForeignKey(
        "clientes.Cliente", on_delete=models.SET_NULL, null=True, blank=True, related_name="facturas"
    )
    concepto = models.CharField(max_length=255)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    fecha_emision = models.DateField(auto_now_add=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Factura {self.numero} - {self.cliente} (${self.monto})"

    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        ordering = ["-fecha_emision"]