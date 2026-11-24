from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver


class Tarea(models.Model):
    """Encargo o trámite que el abogado, la secretaria o el administrador asignan a otra persona del despacho.

    Es lo que ve el dependiente («mis tareas»): presentar escritos, retirar copias, notificar, diligencias...
    """

    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        EN_CURSO = "en_curso", "En curso"
        REALIZADA = "realizada", "Realizada"

    class Tipo(models.TextChoices):
        PRESENTAR_ESCRITO = "presentar_escrito", "Presentar escrito"
        RETIRAR_COPIAS = "retirar_copias", "Retirar copias"
        NOTIFICAR = "notificar", "Notificar"
        DILIGENCIA = "diligencia", "Diligencia"
        REDACTAR = "redactar", "Redactar borrador"
        OTRA = "otra", "Otra"

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.OTRA)
    expediente = models.ForeignKey(
        "expedientes.Expediente", on_delete=models.SET_NULL, null=True, blank=True, related_name="tareas"
    )
    asignado_a = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="tareas_asignadas"
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    fecha_limite = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    fecha_realizada = models.DateTimeField(null=True, blank=True)
    observacion_cierre = models.TextField(blank=True, help_text="Lo que encontró o resolvió quien hizo el trámite")
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tarea"
        verbose_name_plural = "Tareas"
        ordering = ["-creada_en"]

    def __str__(self):
        return self.titulo


class ComprobanteTarea(models.Model):
    """Comprobante o foto de cargo que sube quien hizo el trámite.

    Se guarda igual que los documentos de los expedientes: en la base de datos o, si hay almacenamiento
    externo configurado, allí (ver expedientes/almacenamiento.py).
    """

    tarea = models.ForeignKey(Tarea, on_delete=models.CASCADE, related_name="comprobantes")
    nombre = models.CharField(max_length=255)
    tipo_contenido = models.CharField(max_length=100, blank=True)
    tamano = models.PositiveIntegerField()
    contenido = models.BinaryField(blank=True, default=b"")
    ruta_externa = models.CharField(max_length=500, blank=True, default="")
    subido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    subido_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Comprobante de tarea"
        verbose_name_plural = "Comprobantes de tareas"
        ordering = ["-subido_en"]

    def __str__(self):
        return f"{self.tarea_id} - {self.nombre}"

    def leer_contenido(self):
        """Bytes del archivo, vengan de la base de datos o del almacenamiento externo."""
        if self.ruta_externa:
            from expedientes import almacenamiento

            return almacenamiento.leer(self.ruta_externa)
        return bytes(self.contenido)


@receiver(post_delete, sender=ComprobanteTarea)
def _borrar_archivo_externo(sender, instance, **kwargs):
    if instance.ruta_externa:
        from expedientes import almacenamiento

        almacenamiento.borrar(instance.ruta_externa)
