from django.conf import settings
from django.db import models


class Mensaje(models.Model):
    """Mensaje entre el cliente y el despacho, dentro de un expediente."""

    expediente = models.ForeignKey("expedientes.Expediente", on_delete=models.CASCADE, related_name="mensajes")
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    de_cliente = models.BooleanField(default=False)
    texto = models.TextField(max_length=2000)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mensaje"
        verbose_name_plural = "Mensajes"
        ordering = ["creado_en"]

    def __str__(self):
        return f"{self.expediente_id}: {self.texto[:40]}"
