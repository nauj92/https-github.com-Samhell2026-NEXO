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
from core.permisos import facturas_visibles, puede
from demandas.models import Citacion, ContestacionDemanda, Demanda
from demandas.serializers import CitacionSerializer, ContestacionSerializer, limite_subsanacion
from expedientes.models import EtapaProceso, Expediente
from facturacion.models import Factura
from tareas.models import Tarea
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


def notificar_cliente(cliente, asunto, texto, clave):
    """Avisa al cliente: notificación dentro del portal y correo. Nunca lanza (el correo puede fallar).

    Devuelve cuántas notificaciones internas creó.
    """
    from django.conf import settings
    from django.core.mail import send_mail

    if cliente is None:
        return 0
    usuarios = list(cliente.usuarios_portal.filter(is_active=True))
    creadas = sum(_crear(u, Notificacion.Tipo.GENERAL, texto, clave) for u in usuarios)
    destinos = {cliente.email} if cliente.email else {u.email for u in usuarios if u.email}
    if destinos:
        enlace = f"{settings.FRONTEND_URL.rstrip('/')}/portal"
        cuerpo = f"Hola {cliente.nombre},\n\n{texto}\n\nPuede consultarlo en el portal: {enlace}\n\nACOPROHO"
        try:
            send_mail(asunto, cuerpo, settings.DEFAULT_FROM_EMAIL, sorted(destinos))
        except Exception:
            logger.exception("No se pudo enviar el correo al cliente %s", cliente.pk)
    return creadas


def notificar_despacho_del_cliente(expediente, texto, clave):
    """Avisa al abogado asignado y al equipo de apoyo que el cliente escribió o subió algo."""
    destinos = {expediente.abogado_asignado, *expediente.colaboradores.all()}
    return sum(_crear(u, Notificacion.Tipo.GENERAL, texto, clave) for u in destinos if u is not None)


def _nombre(usuario):
    return usuario.get_full_name() or usuario.username


def notificar_tarea_asignada(tarea, autor):
    """Aviso inmediato al asignado (si no es quien la creó o reasignó)."""
    destino = tarea.asignado_a
    if destino is None or destino.pk == getattr(autor, "pk", None):
        return 0
    return _crear(
        destino, Notificacion.Tipo.TAREA,
        f"{_nombre(autor)} le asignó una tarea: {tarea.titulo}",
        f"tarea:{tarea.pk}:asignada:{destino.pk}",
    )


def notificar_tarea_realizada(tarea, autor):
    """Avisa a quien creó la tarea que ya fue realizada."""
    destino = tarea.creado_por
    if destino is None or destino.pk == getattr(autor, "pk", None):
        return 0
    return _crear(
        destino, Notificacion.Tipo.TAREA,
        f"{_nombre(autor)} marcó como realizada: {tarea.titulo}",
        f"tarea:{tarea.pk}:realizada",
    )


def _texto_escrito(obj, etiqueta):
    partes = [getattr(obj, "clase_proceso", None) or getattr(obj, "destinatario", "")]
    contra = getattr(obj, "demandado", "")
    if contra and getattr(obj, "clase_proceso", None):
        partes.append(contra)
    return f"{etiqueta}: " + " · ".join(p for p in partes if p)


def notificar_borrador_pendiente(obj, etiqueta, autor):
    """Avisa al abogado responsable que hay un escrito esperando su aprobación."""
    destino = obj.abogado_responsable
    if destino is None or destino.pk == getattr(autor, "pk", None):
        return 0
    return _crear(
        destino, Notificacion.Tipo.BORRADOR,
        f"{_nombre(autor)} envió a aprobación — {_texto_escrito(obj, etiqueta)}",
        f"borrador:{etiqueta}:{obj.pk}:{timezone.now():%Y%m%d%H%M%S%f}",
    )


def notificar_borrador_resuelto(obj, etiqueta, autor, aprobado):
    """Avisa a quien envió el escrito si fue aprobado o devuelto."""
    destino = obj.enviado_por
    if destino is None or destino.pk == getattr(autor, "pk", None):
        return 0
    resultado = "aprobó" if aprobado else "devolvió"
    return _crear(
        destino, Notificacion.Tipo.BORRADOR,
        f"{_nombre(autor)} {resultado} — {_texto_escrito(obj, etiqueta)}",
        f"borrador:{etiqueta}:{obj.pk}:{timezone.now():%Y%m%d%H%M%S%f}:{resultado}",
    )


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

    # Facturas: para quienes pueden consultar finanzas, solo las de sus expedientes
    if puede(usuario, "finanzas", "V") and getattr(usuario, "rol", None) != "cliente":
        facturas = facturas_visibles(usuario).filter(
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

    # Tareas asignadas al usuario que vencen pronto o ya vencieron
    if puede(usuario, "tareas", "V"):
        pendientes = Tarea.objects.filter(
            asignado_a=usuario, fecha_limite__isnull=False, fecha_limite__lte=limite
        ).exclude(estado=Tarea.Estado.REALIZADA)
        for tarea in pendientes:
            if tarea.fecha_limite < hoy:
                mensaje = f"Tarea VENCIDA ({tarea.fecha_limite:%d/%m/%Y}): {tarea.titulo}"
                clave = f"tarea:{tarea.pk}:{tarea.fecha_limite}:vencida"
            else:
                mensaje = f"Tarea para {_cuando(tarea.fecha_limite, hoy)}: {tarea.titulo}"
                clave = f"tarea:{tarea.pk}:{tarea.fecha_limite}:proxima"
            creadas += _crear(usuario, Notificacion.Tipo.TAREA, mensaje, clave)

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
