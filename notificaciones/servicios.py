"""Generación automática de notificaciones.

Reglas:
  * Audiencias: aviso cuando una audiencia de un expediente del usuario ocurre
    dentro de los próximos DIAS_AVISO días (incluido hoy).
  * Plazos: aviso cuando una etapa sin completar de un expediente del usuario
    vence dentro de DIAS_AVISO días, y otro aviso distinto cuando ya venció.
  * Facturas (solo administradores y socios): las facturas pendientes con fecha
    de vencimiento pasada se marcan como "vencida" y se avisa; también se avisa
    de las que vencen dentro de DIAS_AVISO días.

Cada aviso se identifica con una `clave`, de modo que ejecutar la generación
varias veces no duplica notificaciones.

Se ejecuta de forma "perezosa" cada vez que el usuario consulta sus
notificaciones, y también se puede programar con:
    python manage.py generar_notificaciones
"""
import logging
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from audiencias.models import Audiencia
from core.permisos import es_directivo
from demandas.models import Citacion, ContestacionDemanda, Demanda
from demandas.serializers import CitacionSerializer, ContestacionSerializer, limite_subsanacion
from expedientes.models import EtapaProceso, Expediente
from facturacion.models import Factura
from vigilancia.models import Vigilancia

from .models import Notificacion

logger = logging.getLogger(__name__)

DIAS_AVISO = 3


def _crear(usuario, tipo, mensaje, clave):
    """Crea la notificación si no existe una con la misma clave. Devuelve 1 si la creó."""
    if Notificacion.objects.filter(usuario=usuario, clave=clave).exists():
        return 0
    Notificacion.objects.create(usuario=usuario, tipo=tipo, mensaje=mensaje[:255], clave=clave)
    return 1


def limite_aviso(hoy):
    return hoy + timedelta(days=DIAS_AVISO)


def _cuando(fecha, hoy):
    dias = (fecha - hoy).days
    if dias == 0:
        return "hoy"
    if dias == 1:
        return "mañana"
    return f"el {fecha:%d/%m/%Y}"


def actualizar_facturas_vencidas(hoy=None):
    """Marca como vencidas las facturas pendientes cuya fecha de vencimiento ya pasó."""
    hoy = hoy or timezone.localdate()
    return Factura.objects.filter(estado=Factura.Estado.PENDIENTE, fecha_vencimiento__lt=hoy).update(
        estado=Factura.Estado.VENCIDA
    )


def generar_para_usuario(usuario, hoy=None):
    """Genera las notificaciones pendientes del usuario. Devuelve cuántas creó."""
    hoy = hoy or timezone.localdate()
    limite = hoy + timedelta(days=DIAS_AVISO)
    creadas = 0

    # Las facturas pendientes con fecha pasada pasan a "vencida" para todos (alimenta Facturación y Reportes)
    actualizar_facturas_vencidas(hoy)

    propios = Expediente.objects.filter(abogado_asignado=usuario).exclude(estado=Expediente.Estado.CERRADO)

    # Audiencias próximas
    audiencias = Audiencia.objects.filter(
        expediente__in=propios, fecha_hora__date__gte=hoy, fecha_hora__date__lte=limite
    ).select_related("expediente")
    for aud in audiencias:
        local = timezone.localtime(aud.fecha_hora)
        mensaje = (
            f"{aud.get_tipo_display()} {_cuando(local.date(), hoy)} a las {local:%H:%M} · "
            f"Exp. {aud.expediente.numero} · {aud.lugar}"
        )
        creadas += _crear(usuario, Notificacion.Tipo.AUDIENCIA, mensaje, f"audiencia:{aud.pk}:{local.date()}")

    # Plazos procesales (etapas con fecha límite)
    etapas = (
        EtapaProceso.objects.filter(expediente__in=propios, fecha_limite__isnull=False, fecha_limite__lte=limite)
        .exclude(estado=EtapaProceso.Estado.COMPLETADA)
        .select_related("expediente")
    )
    for etapa in etapas:
        if etapa.fecha_limite < hoy:
            atraso = (hoy - etapa.fecha_limite).days
            mensaje = f"Plazo VENCIDO hace {atraso} día(s): {etapa.nombre} · Exp. {etapa.expediente.numero}"
            clave = f"plazo:{etapa.pk}:{etapa.fecha_limite}:vencido"
        else:
            mensaje = f"Plazo {_cuando(etapa.fecha_limite, hoy)}: {etapa.nombre} · Exp. {etapa.expediente.numero}"
            clave = f"plazo:{etapa.pk}:{etapa.fecha_limite}:proximo"
        creadas += _crear(usuario, Notificacion.Tipo.PLAZO, mensaje, clave)

    # Demandas inadmitidas: plazo para subsanar
    for demanda in Demanda.objects.filter(abogado_responsable=usuario, estado=Demanda.Estado.INADMITIDA):
        limite = limite_subsanacion(demanda)
        if limite is None or limite > limite_aviso(hoy):
            continue
        if limite < hoy:
            mensaje = f"Plazo para subsanar la demanda VENCIDO hace {(hoy - limite).days} día(s): {demanda.demandante} vs {demanda.demandado}"
            clave = f"subsanacion:{demanda.pk}:{limite}:vencido"
        else:
            mensaje = f"Subsanar la demanda {_cuando(limite, hoy)}: {demanda.demandante} vs {demanda.demandado}"
            clave = f"subsanacion:{demanda.pk}:{limite}:proximo"
        creadas += _crear(usuario, Notificacion.Tipo.PLAZO, mensaje, clave)

    # Contestaciones de demanda (B1): término para contestar
    pendientes = ContestacionDemanda.objects.filter(abogado_responsable=usuario).exclude(
        estado__in=[ContestacionDemanda.Estado.PRESENTADA, ContestacionDemanda.Estado.NO_CONTESTADA]
    )
    for cont in pendientes:
        limite = ContestacionSerializer.limite(cont)
        if limite is None or limite > limite_aviso(hoy):
            continue
        caso = f"{cont.demandante} vs {cont.demandado}"
        if limite < hoy:
            mensaje = f"Término para CONTESTAR la demanda VENCIDO hace {(hoy - limite).days} día(s): {caso}"
            clave = f"contestacion:{cont.pk}:{limite}:vencido"
        else:
            mensaje = f"Contestar la demanda {_cuando(limite, hoy)}: {caso}"
            clave = f"contestacion:{cont.pk}:{limite}:proximo"
        creadas += _crear(usuario, Notificacion.Tipo.PLAZO, mensaje, clave)

    # Citaciones: plazo del demandado para comparecer
    entregadas = Citacion.objects.filter(abogado_responsable=usuario, estado=Citacion.Estado.ENTREGADA)
    for cit in entregadas:
        limite = CitacionSerializer.limite(cit)
        if limite is None or limite > limite_aviso(hoy):
            continue
        if limite < hoy:
            mensaje = f"Venció el plazo para que {cit.destinatario} comparezca a notificarse (hace {(hoy - limite).days} día(s)): considere notificación por aviso"
            clave = f"citacion:{cit.pk}:{limite}:vencido"
        else:
            mensaje = f"{cit.destinatario} puede comparecer a notificarse hasta {_cuando(limite, hoy)}"
            clave = f"citacion:{cit.pk}:{limite}:proximo"
        creadas += _crear(usuario, Notificacion.Tipo.PLAZO, mensaje, clave)

    # Vigilancia judicial: procesos vigilados sin movimiento
    vigilancias = Vigilancia.objects.filter(expediente__in=propios, activa=True).select_related("expediente").prefetch_related(
        "actuaciones"
    )
    for vig in vigilancias:
        if vig.en_alerta(hoy):
            mensaje = f"Vigilancia: Exp. {vig.expediente.numero} sin movimiento hace {vig.dias_sin_movimiento(hoy)} días"
            creadas += _crear(
                usuario, Notificacion.Tipo.GENERAL, mensaje, f"vigilancia:{vig.pk}:{vig.fecha_referencia()}"
            )

    # Facturas: solo para administradores y socios
    if es_directivo(usuario):
        facturas = Factura.objects.filter(
            estado__in=[Factura.Estado.PENDIENTE, Factura.Estado.VENCIDA],
            fecha_vencimiento__isnull=False,
            fecha_vencimiento__lte=limite,
        ).select_related("cliente")
        for fac in facturas:
            cliente = fac.cliente.nombre if fac.cliente else "sin cliente"
            if fac.fecha_vencimiento < hoy:
                mensaje = f"Factura {fac.numero} VENCIDA ({fac.fecha_vencimiento:%d/%m/%Y}) · {cliente}"
                clave = f"factura:{fac.pk}:{fac.fecha_vencimiento}:vencida"
            else:
                mensaje = f"Factura {fac.numero} vence {_cuando(fac.fecha_vencimiento, hoy)} · {cliente}"
                clave = f"factura:{fac.pk}:{fac.fecha_vencimiento}:proxima"
            creadas += _crear(usuario, Notificacion.Tipo.FACTURA, mensaje, clave)

    return creadas


def generar_para_todos(hoy=None):
    """Genera las notificaciones de todos los usuarios activos."""
    total = 0
    for usuario in get_user_model().objects.filter(is_active=True):
        try:
            total += generar_para_usuario(usuario, hoy)
        except Exception:  # un usuario con problemas no debe detener a los demás
            logger.exception("No se pudieron generar notificaciones para %s", usuario)
    return total
