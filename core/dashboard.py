"""Resumen para el tablero (dashboard): lo que el usuario debe atender, respetando su rol."""
import unicodedata
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from audiencias.models import Audiencia
from clientes.models import Cliente
from core.permisos import es_directivo, expedientes_visibles
from core.plazos import sumar_dias_habiles
from demandas.models import ContestacionDemanda, Demanda
from expedientes.models import EtapaProceso

MAX_ITEMS = 8

# Ramas del derecho, en orden de revisión: la primera cuyo texto aparezca gana.
RAMAS = [
    ("Familia", ("FAMILIA",)),
    ("Laboral", ("LABORAL", "TRABAJO")),
    ("Penal", ("PENAL", "ADOLESCENTES", "EJECUCION DE PENAS", "JUSTICIA Y PAZ")),
    ("Administrativo", ("ADMINISTRATIV", "CONTENCIOSO", "SECCION")),
    ("Constitucional", ("CONSTITUCIONAL", "TUTELA")),
    ("Civil", ("CIVIL", "PROMISCUO", "PEQUENAS CAUSAS", "COMERCIAL", "COMPETENCIA MULTIPLE")),
]


def _sin_tildes(texto):
    return "".join(c for c in unicodedata.normalize("NFD", (texto or "").upper()) if unicodedata.category(c) != "Mn")


def rama_de(expediente):
    """Rama del caso: primero la materia que escribió el abogado; si no coincide, la especialidad del despacho."""
    for texto in (expediente.materia, getattr(expediente.juzgado, "especialidad", "")):
        t = _sin_tildes(texto)
        for nombre, claves in RAMAS:
            if any(k in t for k in claves):
                return nombre
    return "Otras"


def _alcance(qs, usuario):
    """Demandas y contestaciones: directivos todo; los demás, lo propio o de sus expedientes."""
    if es_directivo(usuario):
        return qs
    return qs.filter(Q(abogado_responsable=usuario) | Q(expediente__in=expedientes_visibles(usuario)))


class DashboardResumenView(APIView):
    """GET /api/dashboard/resumen/"""

    def get(self, request):
        usuario = request.user
        hoy = timezone.localdate()
        directivo = es_directivo(usuario)

        # Expedientes
        expedientes = expedientes_visibles(usuario)
        por_estado = {e["estado"]: e["total"] for e in expedientes.values("estado").annotate(total=Count("id"))}

        # Audiencias y diligencias de los próximos 30 días
        proximas = (
            Audiencia.objects.filter(
                expediente__in=expedientes, fecha_hora__date__gte=hoy, fecha_hora__date__lte=hoy + timedelta(days=30)
            )
            .select_related("expediente")
            .order_by("fecha_hora")
        )
        audiencias = [
            {
                "id": a.id,
                "tipo": a.get_tipo_display(),
                "clase": a.clase,
                "expediente": a.expediente.numero,
                "fecha_hora": a.fecha_hora.isoformat(),
                "lugar": a.lugar,
            }
            for a in proximas[:MAX_ITEMS]
        ]

        # Etapas procesales vencidas o que vencen en 7 días
        etapas = (
            EtapaProceso.objects.filter(expediente__in=expedientes, fecha_limite__isnull=False, fecha_limite__lte=hoy + timedelta(days=7))
            .exclude(estado=EtapaProceso.Estado.COMPLETADA)
            .select_related("expediente")
            .order_by("fecha_limite")
        )
        plazos = [
            {
                "id": e.id,
                "titulo": e.nombre,
                "referencia": e.expediente.numero,
                "fecha_limite": e.fecha_limite.isoformat(),
                "dias": (e.fecha_limite - hoy).days,
            }
            for e in etapas[:MAX_ITEMS]
        ]

        # Demandas por estado y subsanaciones
        demandas = _alcance(Demanda.objects.all(), usuario)
        demandas_estado = {d["estado"]: d["total"] for d in demandas.values("estado").annotate(total=Count("id"))}

        # Contestaciones pendientes con su fecha límite (días hábiles desde la notificación)
        pendientes = _alcance(
            ContestacionDemanda.objects.exclude(
                estado__in=[ContestacionDemanda.Estado.PRESENTADA, ContestacionDemanda.Estado.NO_CONTESTADA]
            ),
            usuario,
        )
        contestaciones = []
        for c in pendientes:
            if not c.fecha_notificacion:
                continue
            limite = sumar_dias_habiles(c.fecha_notificacion, c.dias_termino)
            contestaciones.append(
                {
                    "id": c.id,
                    "titulo": c.demandado,
                    "referencia": c.demandante,
                    "fecha_limite": limite.isoformat(),
                    "dias": (limite - hoy).days,
                }
            )
        contestaciones.sort(key=lambda x: x["fecha_limite"])
        contestaciones_vencidas = sum(1 for c in contestaciones if c["dias"] < 0)

        # Casos por rama del derecho
        por_rama = {}
        for e in expedientes.select_related("juzgado"):
            r = rama_de(e)
            por_rama[r] = por_rama.get(r, 0) + 1
        casos_por_rama = sorted(({"rama": k, "total": v} for k, v in por_rama.items()), key=lambda x: -x["total"])

        todas_audiencias = Audiencia.objects.filter(expediente__in=expedientes)
        totales = {
            "demandas": demandas.count(),
            "contestaciones": _alcance(ContestacionDemanda.objects.all(), usuario).count(),
            "clientes": Cliente.objects.count(),
            "audiencias": todas_audiencias.filter(tipo=Audiencia.Tipo.AUDIENCIA).count(),
            "diligencias": todas_audiencias.filter(tipo=Audiencia.Tipo.DILIGENCIA).count(),
            "expedientes": expedientes.count(),
        }

        resumen = {
            "totales": totales,
            "casos_por_rama": casos_por_rama,
            "es_directivo": directivo,
            "expedientes": {
                "activos": por_estado.get("activo", 0),
                "tramite": por_estado.get("tramite", 0),
                "cerrados": por_estado.get("cerrado", 0),
            },
            "audiencias_hoy": proximas.filter(fecha_hora__date=hoy).count(),
            "audiencias_proximas": audiencias,
            "plazos": plazos,
            "plazos_vencidos": sum(1 for p in plazos if p["dias"] < 0),
            "demandas_por_estado": demandas_estado,
            "demandas_total": sum(demandas_estado.values()),
            "contestaciones_pendientes": contestaciones[:MAX_ITEMS],
            "contestaciones_pendientes_total": len(contestaciones),
            "contestaciones_vencidas": contestaciones_vencidas,
            "clientes_total": Cliente.objects.count(),
        }
        if directivo:
            resumen["abogados_total"] = get_user_model().objects.filter(is_active=True).count()
            totales["abogados"] = resumen["abogados_total"]
        return Response(resumen)
