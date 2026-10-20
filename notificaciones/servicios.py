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
from expedientes.models import EtapaProceso, Expediente
from facturacion.models import Factura

from .models import Notificacion

logger = logging.getLogger(__name__)

DIAS_AVISO = 3


def _crear(usuario, tipo, mensaje, clave):
    """Crea la notificación si no existe una con la misma clave. Devuelve 1 si la creó."""
    if Notificacion.objects.filter(usuario=usuario, clave=clave).exists():
        return 0
    Notificacion.objects.create(usuario=usuario, tipo=tipo, mensaje=mensaje[:255], clave=clave)
    return 1


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
            f"Audiencia {_cuando(local.date(), hoy)} a las {local:%H:%M} · "
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
