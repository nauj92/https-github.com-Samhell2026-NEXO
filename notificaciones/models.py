from django.conf import settings
from django.db import models


class Notificacion(models.Model):
    class Tipo(models.TextChoices):
        AUDIENCIA = "audiencia", "Audiencia próxima"
        PLAZO = "plazo", "Plazo procesal"
        FACTURA = "factura", "Factura"
        GENERAL = "general", "General"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notificaciones"
    )
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.GENERAL)
    mensaje = models.CharField(max_length=255)
    leida = models.BooleanField(default=False)
    # Identifica el hecho que originó una notificación automática, para no repetirla
    # (p. ej. "audiencia:15:2026-10-21"). Vacía en las notificaciones creadas a mano.
    clave = models.CharField(max_length=120, blank=True, default="", db_index=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario} - {self.mensaje[:40]}"

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ["-creada_en"]