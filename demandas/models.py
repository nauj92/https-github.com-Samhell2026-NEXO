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

    # ---- Requisitos del artículo 82 del Código General del Proceso ----
    class TipoPersona(models.TextChoices):
        NATURAL = "natural", "Persona natural"
        JURIDICA = "juridica", "Persona jurídica o patrimonio autónomo"

    class TipoDocumento(models.TextChoices):
        CC = "CC", "Cédula de ciudadanía"
        CE = "CE", "Cédula de extranjería"
        NIT = "NIT", "NIT"
        PAS = "PAS", "Pasaporte"

    # 1. Juez a quien se dirige
    juez_destinatario = models.CharField(
        max_length=200, blank=True, help_text="Ej.: Juez Civil del Circuito de Cali (Reparto)"
    )
    # 2. Partes
    demandante_tipo_persona = models.CharField(max_length=10, choices=TipoPersona.choices, default=TipoPersona.NATURAL)
    demandante_tipo_documento = models.CharField(max_length=3, choices=TipoDocumento.choices, blank=True)
    demandante_documento = models.CharField(max_length=30, blank=True)
    demandante_domicilio = models.CharField(max_length=200, blank=True)
    demandante_representante = models.CharField(max_length=200, blank=True)
    demandante_representante_documento = models.CharField(max_length=30, blank=True)
    demandado_tipo_persona = models.CharField(max_length=10, choices=TipoPersona.choices, default=TipoPersona.NATURAL)
    demandado_tipo_documento = models.CharField(max_length=3, choices=TipoDocumento.choices, blank=True)
    demandado_documento = models.CharField(max_length=30, blank=True, help_text="Si se conoce")
    demandado_domicilio = models.CharField(max_length=200, blank=True)
    demandado_representante = models.CharField(max_length=200, blank=True)
    demandado_ubicacion_desconocida = models.BooleanField(
        default=False, help_text="Se desconoce el domicilio del demandado o el lugar de notificación (parágrafo 1)"
    )
    otras_partes = models.TextField(blank=True, help_text="Otros demandantes o demandados, con sus datos")
    # 3. Apoderado del demandante
    sin_apoderado = models.BooleanField(default=False, help_text="El demandante actúa sin apoderado judicial")
    apoderado_nombre = models.CharField(max_length=200, blank=True)
    apoderado_documento = models.CharField(max_length=30, blank=True)
    apoderado_tarjeta_profesional = models.CharField(max_length=30, blank=True)
    # 5. Hechos (numerados)
    hechos = models.JSONField(default=list, blank=True, help_text="Lista de hechos; se numeran en el escrito")
    # 6. Pruebas
    pruebas = models.TextField(blank=True, help_text="Pruebas que se pretende hacer valer")
    documentos_en_poder_demandado = models.TextField(
        blank=True, help_text="Documentos que el demandado tiene en su poder, para que los aporte"
    )
    # 7. Juramento estimatorio
    requiere_juramento_estimatorio = models.BooleanField(default=False)
    juramento_estimatorio = models.TextField(blank=True)
    # 8. Fundamentos de derecho
    fundamentos_derecho = models.TextField(blank=True)
    # 9. Cuantía (el valor está en `cuantia`)
    cuantia_aplica = models.BooleanField(
        default=True, help_text="La cuantía es necesaria para determinar competencia o trámite"
    )
    # 10. Notificaciones
    notif_demandante_direccion = models.CharField(max_length=250, blank=True)
    notif_demandante_email = models.EmailField(blank=True)
    notif_demandado_direccion = models.CharField(max_length=250, blank=True)
    notif_demandado_email = models.EmailField(blank=True)
    notif_apoderado_direccion = models.CharField(max_length=250, blank=True)
    notif_apoderado_email = models.EmailField(blank=True)
    # 11. Los demás que exija la ley
    otros_requisitos = models.TextField(
        blank=True, help_text="Conciliación prejudicial, anexos, medidas cautelares y demás exigidos por la ley"
    )

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

    # ---- Requisitos del artículo 96 del Código General del Proceso ----
    demanda = models.ForeignKey(
        Demanda, on_delete=models.SET_NULL, null=True, blank=True, related_name="contestaciones"
    )
    # 1. Demandado y apoderado
    demandado_tipo_persona = models.CharField(max_length=10, choices=Demanda.TipoPersona.choices, default="natural")
    demandado_tipo_documento = models.CharField(max_length=3, choices=Demanda.TipoDocumento.choices, blank=True)
    demandado_documento = models.CharField(max_length=30, blank=True)
    demandado_domicilio = models.CharField(max_length=200, blank=True)
    demandado_representante = models.CharField(max_length=200, blank=True)
    demandado_representante_documento = models.CharField(max_length=30, blank=True)
    sin_apoderado = models.BooleanField(default=False)
    apoderado_nombre = models.CharField(max_length=200, blank=True)
    apoderado_documento = models.CharField(max_length=30, blank=True)
    apoderado_tarjeta_profesional = models.CharField(max_length=30, blank=True)
    apoderado_domicilio = models.CharField(max_length=200, blank=True)
    # 2. Pronunciamiento sobre pretensiones y hechos
    pronunciamiento_pretensiones = models.TextField(blank=True)
    pronunciamientos_hechos = models.JSONField(default=list, blank=True)
    # 3. Excepciones de mérito, juramento estimatorio y derecho de retención
    excepciones_merito = models.JSONField(default=list, blank=True)
    sin_excepciones = models.BooleanField(default=False)
    objeta_juramento_estimatorio = models.BooleanField(default=False)
    objecion_juramento = models.TextField(blank=True)
    alega_derecho_retencion = models.BooleanField(default=False)
    derecho_retencion = models.TextField(blank=True)
    # 4. Pruebas (el campo `pruebas` ya existía)
    pruebas_en_expediente = models.BooleanField(default=False)
    # 5. Notificaciones
    notif_demandado_direccion = models.CharField(max_length=250, blank=True)
    notif_demandado_email = models.EmailField(blank=True)
    notif_apoderado_direccion = models.CharField(max_length=250, blank=True)
    notif_apoderado_email = models.EmailField(blank=True)
    # Anexos
    anexo_poder = models.BooleanField(default=False)
    anexo_existencia_representacion = models.BooleanField(default=False)
    documentos_solicitados = models.TextField(blank=True)
    anexos_otros = models.TextField(blank=True)

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
