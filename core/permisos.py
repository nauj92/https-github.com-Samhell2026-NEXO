"""Permisos y alcance de datos por rol.

Regla del sistema (ver informe, sección 6.1):
  * administrador y socio_director -> ven y gestionan todo.
  * abogado y secretario_juridico  -> solo ven lo que pertenece a los
    expedientes que tienen asignados.

Toda vista que muestre datos de expedientes (etapas, audiencias, facturas,
estadísticas) debe partir de `expedientes_visibles()` para respetar la regla.
"""
from rest_framework import serializers
from rest_framework.permissions import BasePermission

ROLES_DIRECTIVOS = ("administrador", "socio_director")


def es_directivo(usuario):
    """True si el usuario tiene acceso total (administrador, socio o superusuario)."""
    if usuario is None or not getattr(usuario, "is_authenticated", False):
        return False
    return bool(usuario.is_superuser or getattr(usuario, "rol", None) in ROLES_DIRECTIVOS)


class EsDirectivo(BasePermission):
    """Solo administradores y socios directores."""

    message = "No tiene permisos para realizar esta acción."

    def has_permission(self, request, view):
        return es_directivo(request.user)


def expedientes_visibles(usuario):
    """Queryset de expedientes que el usuario puede ver."""
    from expedientes.models import Expediente

    if es_directivo(usuario):
        return Expediente.objects.all()
    return Expediente.objects.filter(abogado_asignado=usuario)


def facturas_visibles(usuario):
    """Queryset de facturas que el usuario puede ver (las de sus expedientes; los directivos, todas)."""
    from facturacion.models import Factura

    if es_directivo(usuario):
        return Factura.objects.all()
    return Factura.objects.filter(expediente__in=expedientes_visibles(usuario))


def exigir_expediente_visible(request, expediente):
    """Lanza ValidationError si el usuario no tiene acceso al expediente dado."""
    if request is None or expediente is None:
        return
    if not expedientes_visibles(request.user).filter(pk=expediente.pk).exists():
        raise serializers.ValidationError("No tiene acceso a ese expediente.")
