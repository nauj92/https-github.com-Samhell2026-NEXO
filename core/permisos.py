"""Permisos y alcance de datos por rol.

Regla del sistema (ver informe, sección 6.1):
  * administrador y socio_director -> ven y gestionan todo.
  * abogado y secretario_juridico  -> solo ven lo que pertenece a los
    expedientes que tienen asignados.

Toda vista que muestre datos de expedientes (etapas, audiencias, facturas,
estadísticas) debe partir de `expedientes_visibles()` para respetar la regla.
"""
from rest_framework import serializers
from rest_framework.permissions import BasePermission, IsAuthenticated

ROLES_DIRECTIVOS = ("administrador", "socio_director")


def es_directivo(usuario):
    """True si el usuario tiene acceso total (administrador, socio o superusuario)."""
    if usuario is None or not getattr(usuario, "is_authenticated", False):
        return False
    return bool(usuario.is_superuser or getattr(usuario, "rol", None) in ROLES_DIRECTIVOS)


def es_administrador(usuario):
    """True solo para el administrador (o superusuario): es quien crea y gestiona los usuarios."""
    if usuario is None or not getattr(usuario, "is_authenticated", False):
        return False
    return bool(usuario.is_superuser or getattr(usuario, "rol", None) == "administrador")


def primer_ingreso_pendiente(usuario):
    """True si el usuario aún debe cambiar la contraseña inicial o autorizar el tratamiento de sus datos."""
    return bool(
        getattr(usuario, "debe_cambiar_password", False) or getattr(usuario, "autorizacion_datos_pendiente", False)
    )


MENSAJE_PRIMER_INGRESO = "Debe cambiar su contraseña y autorizar el tratamiento de datos antes de continuar."


class AccesoCompleto(IsAuthenticated):
    """Permiso por defecto: usuario autenticado que ya completó su primer ingreso.

    * Mientras tenga pendiente el cambio de contraseña o la autorización de datos, solo puede usar las vistas
      marcadas con `permitido_en_primer_ingreso = True` (perfil, cambio de contraseña, autorización).
    * Los usuarios con rol «cliente» solo acceden a las vistas marcadas con `permitido_en_primer_ingreso`
      o `acceso_cliente`; el resto del sistema es para el personal del despacho.
    """

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if getattr(view, "permitido_en_primer_ingreso", False):
            return True
        usuario = request.user
        if primer_ingreso_pendiente(usuario):
            self.message = MENSAJE_PRIMER_INGRESO
            return False
        if getattr(usuario, "rol", None) == "cliente" and not getattr(view, "acceso_cliente", False):
            self.message = "Su cuenta de cliente no tiene acceso a esta sección."
            return False
        return True


class EsDirectivo(BasePermission):
    """Solo administradores y socios directores."""

    message = "No tiene permisos para realizar esta acción."

    def has_permission(self, request, view):
        return es_directivo(request.user) and not primer_ingreso_pendiente(request.user)


class EsAdministrador(BasePermission):
    """Solo el administrador: crear y modificar usuarios."""

    message = "Solo el administrador puede crear o modificar usuarios."

    def has_permission(self, request, view):
        return es_administrador(request.user) and not primer_ingreso_pendiente(request.user)


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
