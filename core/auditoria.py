"""Auditoría: quién hizo qué y cuándo. Solo el administrador (módulo «auditoria» de la matriz).

Reúne el historial de cambios de los expedientes (datos, documentos, etapas, tareas, portal) y los inicios de
sesión (django-axes), sin tocar los datos: es de solo lectura.
"""
from datetime import datetime, time

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from expedientes.models import EventoExpediente, Expediente

LIMITE = 300
TIPOS_HISTORIAL = {"+": "Expediente creado", "~": "Expediente modificado", "-": "Expediente eliminado"}


def _fecha(texto, fin=False):
    try:
        dia = datetime.strptime(texto, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None
    return timezone.make_aware(datetime.combine(dia, time.max if fin else time.min))


def _nombre(usuario):
    if usuario is None:
        return "Sistema"
    return usuario.get_full_name() or usuario.username


class AuditoriaView(APIView):
    """GET /api/auditoria/?usuario=ID&desde=AAAA-MM-DD&hasta=AAAA-MM-DD -> {actividad: [...], accesos: [...]}"""

    modulo = "auditoria"

    def get(self, request):
        params = request.query_params
        usuario_id = params.get("usuario") if (params.get("usuario") or "").isdigit() else None
        desde, hasta = _fecha(params.get("desde")), _fecha(params.get("hasta"), fin=True)

        eventos = EventoExpediente.objects.select_related("expediente", "usuario")
        historial = Expediente.history.select_related("history_user")
        if usuario_id:
            eventos = eventos.filter(usuario_id=usuario_id)
            historial = historial.filter(history_user_id=usuario_id)
        if desde:
            eventos, historial = eventos.filter(fecha__gte=desde), historial.filter(history_date__gte=desde)
        if hasta:
            eventos, historial = eventos.filter(fecha__lte=hasta), historial.filter(history_date__lte=hasta)

        actividad = []
        for e in eventos.order_by("-fecha")[:LIMITE]:
            detalle = "; ".join(
                f"{c.get('campo')}: {c.get('anterior')} → {c.get('nuevo')}" for c in (e.cambios or [])
            )
            actividad.append(
                {"fecha": e.fecha, "usuario": _nombre(e.usuario), "accion": e.tipo,
                 "expediente": e.expediente.numero, "detalle": detalle}
            )
        for h in historial.order_by("-history_date")[:LIMITE]:
            actividad.append(
                {"fecha": h.history_date, "usuario": _nombre(h.history_user),
                 "accion": TIPOS_HISTORIAL.get(h.history_type, "Cambio"), "expediente": h.numero, "detalle": ""}
            )
        actividad.sort(key=lambda a: a["fecha"], reverse=True)

        return Response({"actividad": actividad[:LIMITE], "accesos": self._accesos(usuario_id, desde, hasta)})

    @staticmethod
    def _accesos(usuario_id, desde, hasta):
        """Inicios de sesión registrados por django-axes y cuentas con intentos fallidos."""
        try:
            from axes.models import AccessAttempt, AccessLog
        except Exception:  # axes no instalado o cambió su API: la auditoría de actividad sigue funcionando
            return {"inicios": [], "fallidos": []}
        logs = AccessLog.objects.all()
        if usuario_id:
            usuario = get_user_model().objects.filter(pk=usuario_id).first()
            logs = logs.filter(username=usuario.username) if usuario else logs.none()
        if desde:
            logs = logs.filter(attempt_time__gte=desde)
        if hasta:
            logs = logs.filter(attempt_time__lte=hasta)
        inicios = [
            {"fecha": l.attempt_time, "usuario": l.username, "ip": l.ip_address, "cierre": l.logout_time}
            for l in logs.order_by("-attempt_time")[:LIMITE]
        ]
        fallidos = [
            {"fecha": a.attempt_time, "usuario": a.username, "ip": a.ip_address, "intentos": a.failures_since_start}
            for a in AccessAttempt.objects.order_by("-attempt_time")[:50]
        ]
        return {"inicios": inicios, "fallidos": fallidos}
