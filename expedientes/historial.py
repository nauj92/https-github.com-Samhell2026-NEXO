"""Historial de cambios de un expediente, a partir de django-simple-history."""
from django.contrib.auth import get_user_model

from clientes.models import Cliente

from .models import Juzgado

# Campo -> etiqueta legible
CAMPOS = {
    "numero": "Radicado",
    "juzgado_id": "Juzgado",
    "cliente_id": "Cliente",
    "demandante": "Demandante",
    "demandado": "Demandado",
    "materia": "Materia",
    "estado": "Estado",
    "abogado_asignado_id": "Abogado asignado",
}
ESTADOS = {"activo": "Activo", "tramite": "En trámite", "cerrado": "Cerrado"}
TIPOS = {"+": "Creación", "~": "Modificación", "-": "Eliminación"}


def _nombres(registros):
    """Resuelve en bloque los nombres de juzgados, clientes y abogados citados."""
    Usuario = get_user_model()
    juzgados = {getattr(r, "juzgado_id") for r in registros} - {None}
    clientes = {getattr(r, "cliente_id") for r in registros} - {None}
    abogados = {getattr(r, "abogado_asignado_id") for r in registros} - {None}
    return {
        "juzgado_id": {j.pk: j.nombre for j in Juzgado.objects.filter(pk__in=juzgados)},
        "cliente_id": {c.pk: c.nombre for c in Cliente.objects.filter(pk__in=clientes)},
        "abogado_asignado_id": {
            u.pk: (u.get_full_name() or u.username) for u in Usuario.objects.filter(pk__in=abogados)
        },
    }


def _legible(campo, valor, nombres):
    if valor in (None, ""):
        return "—"
    if campo == "estado":
        return ESTADOS.get(valor, valor)
    if campo in nombres:
        return nombres[campo].get(valor, f"(registro {valor} eliminado)")
    return str(valor)


def historial_de(expediente):
    """Lista de eventos, del más reciente al más antiguo, con los cambios de cada uno."""
    registros = list(expediente.history.select_related("history_user").order_by("-history_date", "-history_id"))
    nombres = _nombres(registros)
    eventos = []
    for i, reg in enumerate(registros):
        anterior = registros[i + 1] if i + 1 < len(registros) else None
        cambios = []
        if reg.history_type == "~" and anterior is not None:
            for campo, etiqueta in CAMPOS.items():
                antes, despues = getattr(anterior, campo), getattr(reg, campo)
                if antes != despues:
                    cambios.append(
                        {
                            "campo": etiqueta,
                            "anterior": _legible(campo, antes, nombres),
                            "nuevo": _legible(campo, despues, nombres),
                        }
                    )
        usuario = reg.history_user
        eventos.append(
            {
                "fecha": reg.history_date,
                "tipo": TIPOS.get(reg.history_type, reg.history_type),
                "usuario": (usuario.get_full_name() or usuario.username) if usuario else "Sistema",
                "cambios": cambios,
            }
        )
    return eventos
