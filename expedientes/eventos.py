"""Registro de eventos de un expediente (documentos y etapas) para el historial de cambios."""
from .models import EventoExpediente

ESTADOS_ETAPA = {"pendiente": "Pendiente", "en_curso": "En curso", "completada": "Completada"}


def registrar(expediente, usuario, tipo, cambios):
    """Guarda un evento. `cambios` es una lista de (campo, anterior, nuevo)."""
    EventoExpediente.objects.create(
        expediente=expediente,
        tipo=tipo,
        usuario=usuario if getattr(usuario, "is_authenticated", False) else None,
        cambios=[{"campo": c, "anterior": a, "nuevo": n} for c, a, n in cambios],
    )


def _texto_etapa(etapa):
    return f"{etapa.nombre} ({etapa.fecha_limite:%d/%m/%Y})" if etapa.fecha_limite else etapa.nombre


def instantanea_etapa(etapa):
    return {"nombre": etapa.nombre, "fecha_limite": etapa.fecha_limite, "estado": etapa.estado}


def cambios_de_etapa(antes, etapa):
    """Diferencias entre la instantánea previa y el estado actual de la etapa."""
    cambios = []
    rotulo = f"Etapa «{antes['nombre']}»"
    if antes["nombre"] != etapa.nombre:
        cambios.append((f"{rotulo} · Nombre", antes["nombre"], etapa.nombre))
    if antes["estado"] != etapa.estado:
        cambios.append((f"{rotulo} · Estado", ESTADOS_ETAPA.get(antes["estado"], antes["estado"]), ESTADOS_ETAPA.get(etapa.estado, etapa.estado)))
    if antes["fecha_limite"] != etapa.fecha_limite:
        fmt = lambda d: d.strftime("%d/%m/%Y") if d else "—"
        cambios.append((f"{rotulo} · Fecha límite", fmt(antes["fecha_limite"]), fmt(etapa.fecha_limite)))
    return cambios


def texto_etapa(etapa):
    return _texto_etapa(etapa)
