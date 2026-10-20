from django.conf import settings
from django.db import models


class Demanda(models.Model):
    """Seguimiento de una demanda desde su elaboración hasta su admisión (o rechazo)."""

    class Estado(models.TextChoices):
        ELABORACION = "elaboracion", "En elaboración"
        RADICADA = "radicada", "Radicada"
        INADMITIDA = "inadmitida", "Inadmitida (subsanar)"
        ADMITIDA = "admitida", "Admitida"
        RECHAZADA = "rechazada", "Rechazada"
        RETIRADA = "retirada", "Retirada"

    clase_proceso = models.CharField(max_length=150, help_text="Ej.: Ejecutivo singular, Ordinario laboral")
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.SET_NULL, null=True, blank=True, related_name="demandas")
    expediente = models.ForeignKey(
        "expedientes.Expediente", on_delete=models.SET_NULL, null=True, blank=True, related_name="demandas"
    )
    juzgado = models.ForeignKey("expedientes.Juzgado", on_delete=models.SET_NULL, null=True, blank=True, related_name="demandas")
    demandante = models.CharField(max_length=200)
    demandado = models.CharField(max_length=200)
    pretensiones = models.TextField()
    cuantia = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ELABORACION)
    fecha_radicacion = models.DateField(null=True, blank=True)
    fecha_inadmision = models.DateField(null=True, blank=True)
    fecha_admision = models.DateField(null=True, blank=True)
    abogado_responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="demandas"
    )
    borrador = models.TextField(blank=True, help_text="Borrador del escrito de demanda (editable)")
    observaciones = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Demanda"
        verbose_name_plural = "Demandas"
        ordering = ["-creado_en"]

    def __str__(self):
        return f"{self.clase_proceso}: {self.demandante} vs {self.demandado}"


class ContestacionDemanda(models.Model):
    """B1: contestación de una demanda en la que el cliente del despacho es el demandado."""

    class Estado(models.TextChoices):
        POR_ELABORAR = "por_elaborar", "Por elaborar"
        EN_ELABORACION = "en_elaboracion", "En elaboración"
        PRESENTADA = "presentada", "Presentada"
        NO_CONTESTADA = "no_contestada", "No contestada"

    clase_proceso = models.CharField(max_length=150)
    demandante = models.CharField(max_length=200)
    demandado = models.CharField(max_length=200, help_text="Normalmente el cliente del despacho")
    cliente = models.ForeignKey(
        "clientes.Cliente", on_delete=models.SET_NULL, null=True, blank=True, related_name="contestaciones"
    )
    expediente = models.ForeignKey(
        "expedientes.Expediente", on_delete=models.SET_NULL, null=True, blank=True, related_name="contestaciones"
    )
    juzgado = models.ForeignKey(
        "expedientes.Juzgado", on_delete=models.SET_NULL, null=True, blank=True, related_name="contestaciones"
    )
    fecha_notificacion = models.DateField(null=True, blank=True, help_text="Cuando quedó notificada la demanda")
    dias_termino = models.PositiveSmallIntegerField(default=20, help_text="Días hábiles de traslado")
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.POR_ELABORAR)
    fecha_presentacion = models.DateField(null=True, blank=True)
    excepciones = models.TextField(blank=True, help_text="Excepciones de mérito y previas")
    pruebas = models.TextField(blank=True)
    borrador = models.TextField(blank=True)
    abogado_responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="contestaciones"
    )
    observaciones = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Contestación de demanda"
        verbose_name_plural = "Contestaciones de demanda"
        ordering = ["-creado_en"]

    def __str__(self):
        return f"Contestación: {self.demandante} vs {self.demandado}"


class Citacion(models.Model):
    """Citación al demandado para notificarse (art. 291 CGP) o notificación por aviso (art. 292 CGP)."""

    class Tipo(models.TextChoices):
        CITACION = "citacion", "Citación para notificación personal (art. 291)"
        AVISO = "aviso", "Notificación por aviso (art. 292)"

    class Ubicacion(models.TextChoices):
        MISMO_MUNICIPIO = "mismo_municipio", "Mismo municipio del juzgado"
        OTRO_MUNICIPIO = "otro_municipio", "Otro municipio del país"
        EXTERIOR = "exterior", "En el exterior"

    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente de envío"
        ENVIADA = "enviada", "Enviada"
        ENTREGADA = "entregada", "Entregada"
        DEVUELTA = "devuelta", "Devuelta (no entregada)"
        NOTIFICADO = "notificado", "Notificado"

    demanda = models.ForeignKey(Demanda, on_delete=models.SET_NULL, null=True, blank=True, related_name="citaciones")
    expediente = models.ForeignKey(
        "expedientes.Expediente", on_delete=models.SET_NULL, null=True, blank=True, related_name="citaciones"
    )
    destinatario = models.CharField(max_length=200)
    direccion = models.CharField(max_length=250, blank=True)
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.CITACION)
    ubicacion = models.CharField(max_length=20, choices=Ubicacion.choices, default=Ubicacion.MISMO_MUNICIPIO)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    fecha_envio = models.DateField(null=True, blank=True)
    empresa_mensajeria = models.CharField(max_length=100, blank=True)
    guia = models.CharField(max_length=60, blank=True)
    fecha_entrega = models.DateField(null=True, blank=True)
    fecha_notificacion = models.DateField(null=True, blank=True, help_text="Cuando el demandado se notificó personalmente")
    abogado_responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="citaciones"
    )
    observaciones = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Citación"
        verbose_name_plural = "Citaciones"
        ordering = ["-creado_en"]

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.destinatario}"
