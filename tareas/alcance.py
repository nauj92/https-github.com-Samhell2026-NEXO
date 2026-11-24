from django.db.models import Q

from core.permisos import es_directivo, expedientes_visibles, puede

from .models import Tarea


def tareas_visibles(usuario):
    """Tareas que el usuario puede ver: las suyas (asignadas o creadas) y, si crea tareas, las de sus expedientes."""
    qs = Tarea.objects.all()
    if es_directivo(usuario):
        return qs
    filtro = Q(asignado_a=usuario) | Q(creado_por=usuario)
    if puede(usuario, "tareas", "C"):
        filtro |= Q(expediente__in=expedientes_visibles(usuario))
    return qs.filter(filtro).distinct()
