from django.conf import settings
from django.db import models
from django.utils import timezone


class Vigilancia(models.Model):
    """Seguimiento de un proceso: se registran las actuaciones y se alerta si pasa mucho tiempo sin movimiento."""

    expediente = models.OneToOneField("expedientes.Expediente", on_delete=models.CASCADE, related_name="vigilancia")
    activa = models.BooleanField(default=True)
    dias_alerta = models.PositiveSmallIntegerField(
        default=30, help_text="Días sin movimiento tras los cuales se genera una alerta"
    )
    observaciones = models.TextField(blank=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="vigilancias_creadas"
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Vigilancia judicial"
        verbose_name_plural = "Vigilancias judiciales"
        ordering = ["-creado_en"]

    def __str__(self):
        return f"Vigilancia {self.expediente.numero}"

    def ultima_actuacion(self):
        # Usa lo ya cargado con prefetch_related para evitar una consulta por fila
        actuaciones = list(self.actuaciones.all())
        return max(actuaciones, key=lambda a: (a.fecha, a.pk)) if actuaciones else None

    def fecha_referencia(self):
        """Fecha desde la que se cuentan los días sin movimiento: la última actuación o, si no hay, el alta."""
        ultima = self.ultima_actuacion()
        return ultima.fecha if ultima else timezone.localtime(self.creado_en).date()

    def dias_sin_movimiento(self, hoy=None):
        hoy = hoy or timezone.localdate()
        return max(0, (hoy - self.fecha_referencia()).days)

    def en_alerta(self, hoy=None):
        return self.activa and self.dias_sin_movimiento(hoy) >= self.dias_alerta


class ActuacionVigilancia(models.Model):
    vigilancia = models.ForeignKey(Vigilancia, on_delete=models.CASCADE, related_name="actuaciones")
    fecha = models.DateField()
    descripcion = models.CharField(max_length=500)
    registrada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="actuaciones_registradas"
    )
    registrada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Actuación"
        verbose_name_plural = "Actuaciones"
        ordering = ["-fecha", "-id"]

    def __str__(self):
        return f"{self.fecha} - {self.descripcion[:40]}"


class EnlaceVigilancia(models.Model):
    """Enlace anclado a un proceso vigilado (consulta de la Rama Judicial, un auto, un expediente digital...)."""

    vigilancia = models.ForeignKey(Vigilancia, on_delete=models.CASCADE, related_name="enlaces")
    titulo = models.CharField(max_length=150)
    url = models.URLField(max_length=1000)
    nota = models.CharField(max_length=300, blank=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="enlaces_vigilancia"
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Enlace anclado"
        verbose_name_plural = "Enlaces anclados"
        ordering = ["-creado_en"]

    def __str__(self):
        return self.titulo
