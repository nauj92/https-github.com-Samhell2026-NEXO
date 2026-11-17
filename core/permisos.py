"""Roles, permisos por módulo y alcance de datos.

Fuente: documento «Roles y permisos ACOPROHO» (matriz del ingeniero).

Orden de permisos: Cliente < Dependiente < Escribiente < Secretaria < Abogado < Administrador.

Alcance de datos (qué expedientes ve cada rol):
  * administrador y abogado socio -> todos los expedientes.
  * abogado                       -> los que tiene asignados (`abogado_asignado`).
  * secretaria y escribiente      -> los expedientes en cuyo equipo de apoyo (`colaboradores`) están.
  * dependiente                   -> ninguno (solo sus tareas y trámites).
  * cliente                       -> solo lo suyo, en lectura (portal del cliente).

Permisos por módulo (MATRIZ): V ver · C crear · E editar · X eliminar · A aprobar.

Toda vista que muestre datos de expedientes (etapas, audiencias, facturas, estadísticas) debe partir de
`expedientes_visibles()` para respetar el alcance. Toda vista que pertenezca a un módulo de la matriz declara
`modulo = "..."`: `AccesoCompleto` (permiso por defecto) comprueba entonces el permiso V/C/E/X de la acción.
"""
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission, IsAuthenticated

ROL_ADMINISTRADOR = "administrador"
ROL_ABOGADO = "abogado"
ROL_SECRETARIA = "secretario_juridico"
ROL_ESCRIBIENTE = "escribiente"
ROL_DEPENDIENTE = "dependiente"
ROL_CLIENTE = "cliente"

# Roles con acceso total por sí mismos (el abogado socio también lo tiene, ver `es_directivo`).
ROLES_DIRECTIVOS = (ROL_ADMINISTRADOR,)

TODOS_LOS_PERMISOS = "VCEXA"

# modulo -> rol -> letras. Un rol que no aparece no tiene acceso al módulo.
MATRIZ = {
    # Gestión de cuentas y roles
    "usuarios": {ROL_ADMINISTRADOR: "VCEX"},
    "clientes": {
        ROL_ADMINISTRADOR: "VCEX", ROL_ABOGADO: "VCE", ROL_SECRETARIA: "VCE", ROL_ESCRIBIENTE: "V", ROL_CLIENTE: "V",
    },
    # Expedientes (la secretaria solo modifica datos básicos; ver ExpedienteSerializer)
    "expedientes": {
        ROL_ADMINISTRADOR: "VCEX", ROL_ABOGADO: "VCEA", ROL_SECRETARIA: "VCE", ROL_ESCRIBIENTE: "V", ROL_CLIENTE: "V",
    },
    # Documentos y escritos (demandas, contestaciones, citaciones y archivos adjuntos).
    # El escribiente solo crea y edita borradores; el dependiente solo sube comprobantes.
    "documentos": {
        ROL_ADMINISTRADOR: "VCEX", ROL_ABOGADO: "VCEA", ROL_SECRETARIA: "VCE", ROL_ESCRIBIENTE: "VCE",
        ROL_DEPENDIENTE: "C", ROL_CLIENTE: "V",
    },
    # Agenda y plazos (audiencias, diligencias y etapas con fecha límite)
    "agenda": {
        ROL_ADMINISTRADOR: "VCEX", ROL_ABOGADO: "VCE", ROL_SECRETARIA: "VCEX", ROL_ESCRIBIENTE: "V",
        ROL_DEPENDIENTE: "V", ROL_CLIENTE: "V",
    },
    # Facturación y finanzas (facturas y acuerdos de pago)
    "finanzas": {ROL_ADMINISTRADOR: "VCEX", ROL_ABOGADO: "V", ROL_SECRETARIA: "V", ROL_CLIENTE: "V"},
    # Liquidaciones (herramienta de cálculo jurídico). No está en la matriz del ingeniero: supuesto por confirmar.
    "liquidaciones": {ROL_ADMINISTRADOR: "VCEX", ROL_ABOGADO: "VCE", ROL_SECRETARIA: "V", ROL_ESCRIBIENTE: "V"},
    # Vigilancia judicial. No está en la matriz del ingeniero: se trata como parte de los expedientes.
    "vigilancia": {ROL_ADMINISTRADOR: "VCEX", ROL_ABOGADO: "VCE", ROL_SECRETARIA: "VCE", ROL_ESCRIBIENTE: "V"},
    # Reportes: tablero de resumen
    "reportes": {ROL_ADMINISTRADOR: "V", ROL_ABOGADO: "V", ROL_SECRETARIA: "V"},
    # Auditoría y registros del sistema
    "auditoria": {ROL_ADMINISTRADOR: "V"},
}

MENSAJE_SIN_PERMISO = "Su rol no tiene permiso para realizar esta acción."


def _autenticado(usuario):
    return usuario is not None and getattr(usuario, "is_authenticated", False)


def es_administrador(usuario):
    """True solo para el administrador (o superusuario): gestiona usuarios, roles y la configuración."""
    if not _autenticado(usuario):
        return False
    return bool(usuario.is_superuser or getattr(usuario, "rol", None) == ROL_ADMINISTRADOR)


def es_socio(usuario):
    """True si es un abogado marcado como socio."""
    if not _autenticado(usuario):
        return False
    return bool(getattr(usuario, "rol", None) == ROL_ABOGADO and getattr(usuario, "es_socio", False))


def es_directivo(usuario):
    """True si ve todos los expedientes del despacho: administrador, abogado socio o superusuario."""
    return es_administrador(usuario) or es_socio(usuario)


def permisos_de(usuario):
    """Permisos del usuario por módulo, p. ej. {"clientes": "VCE", ...} (solo módulos con acceso)."""
    if not _autenticado(usuario):
        return {}
    if usuario.is_superuser:
        return {modulo: TODOS_LOS_PERMISOS for modulo in MATRIZ}
    rol = getattr(usuario, "rol", None)
    return {modulo: roles[rol] for modulo, roles in MATRIZ.items() if rol in roles}


def puede(usuario, modulo, letra):
    """True si el rol del usuario tiene la letra (V, C, E, X o A) en el módulo."""
    return letra in permisos_de(usuario).get(modulo, "")


def exigir_permiso(usuario, modulo, letra):
    """Lanza PermissionDenied (403) si el rol no tiene ese permiso."""
    if not puede(usuario, modulo, letra):
        raise PermissionDenied(MENSAJE_SIN_PERMISO)


def primer_ingreso_pendiente(usuario):
    """True si el usuario aún debe cambiar la contraseña inicial o autorizar el tratamiento de sus datos."""
    return bool(
        getattr(usuario, "debe_cambiar_password", False) or getattr(usuario, "autorizacion_datos_pendiente", False)
    )


MENSAJE_PRIMER_INGRESO = "Debe cambiar su contraseña y autorizar el tratamiento de datos antes de continuar."

_LETRA_POR_ACCION = {
    "list": "V", "retrieve": "V", "create": "C", "update": "E", "partial_update": "E", "destroy": "X",
}
_LETRA_POR_METODO = {"GET": "V", "HEAD": "V", "OPTIONS": "V", "POST": "C", "PUT": "E", "PATCH": "E", "DELETE": "X"}


def permiso_requerido(request, view):
    """(módulo, letra) que exige la petición, o None si la vista no declara `modulo`.

    La vista puede declarar `permisos_accion = {nombre_de_la_acción: X}` para las acciones propias, donde X es:
      * una letra ("E"),
      * una pareja ("documentos", "C") si la acción pertenece a otro módulo, o
      * un diccionario por método HTTP: {"GET": ("documentos", "V"), "POST": ("documentos", "C")}.
    Sin declaración, la letra sale de la acción estándar (list, create...) o del método HTTP.
    """
    modulo = getattr(view, "modulo", None)
    if not modulo:
        return None
    accion = getattr(view, "action", None)
    especial = (getattr(view, "permisos_accion", None) or {}).get(accion)
    if isinstance(especial, dict):
        especial = especial.get(request.method)
    if isinstance(especial, tuple):
        return especial
    if isinstance(especial, str):
        return modulo, especial
    return modulo, _LETRA_POR_ACCION.get(accion) or _LETRA_POR_METODO.get(request.method, "E")


class AccesoCompleto(IsAuthenticated):
    """Permiso por defecto: usuario autenticado que ya completó su primer ingreso.

    * Mientras tenga pendiente el cambio de contraseña o la autorización de datos, solo puede usar las vistas
      marcadas con `permitido_en_primer_ingreso = True` (perfil, cambio de contraseña, autorización).
    * Los usuarios con rol «cliente» solo acceden a las vistas marcadas con `permitido_en_primer_ingreso`
      o `acceso_cliente`; el resto del sistema es para el personal del despacho.
    * Si la vista declara `modulo`, además se exige el permiso V/C/E/X que la matriz da al rol (ver MATRIZ).
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
        if getattr(usuario, "rol", None) == ROL_CLIENTE and not getattr(view, "acceso_cliente", False):
            self.message = "Su cuenta de cliente no tiene acceso a esta sección."
            return False
        requerido = permiso_requerido(request, view)
        if requerido is not None and not puede(usuario, *requerido):
            self.message = MENSAJE_SIN_PERMISO
            return False
        return True


def permiso_de(modulo, letra):
    """Clase de permiso DRF: el rol debe tener esa letra en el módulo (para vistas con permisos mixtos)."""

    class _PermisoDeModulo(BasePermission):
        message = MENSAJE_SIN_PERMISO

        def has_permission(self, request, view):
            return puede(request.user, modulo, letra) and not primer_ingreso_pendiente(request.user)

    return _PermisoDeModulo


class EsDirectivo(BasePermission):
    """Solo quienes ven todo el despacho: administrador y abogado socio."""

    message = "No tiene permisos para realizar esta acción."

    def has_permission(self, request, view):
        return es_directivo(request.user) and not primer_ingreso_pendiente(request.user)


class EsAdministrador(BasePermission):
    """Solo el administrador: crear y modificar usuarios."""

    message = "Solo el administrador puede realizar esta acción."

    def has_permission(self, request, view):
        return es_administrador(request.user) and not primer_ingreso_pendiente(request.user)


def expedientes_visibles(usuario):
    """Queryset de expedientes que el usuario puede ver, según su rol."""
    from expedientes.models import Expediente

    if es_directivo(usuario):
        return Expediente.objects.all()
    rol = getattr(usuario, "rol", None)
    if rol == ROL_ABOGADO:
        return Expediente.objects.filter(abogado_asignado=usuario)
    if rol in (ROL_SECRETARIA, ROL_ESCRIBIENTE):
        return Expediente.objects.filter(colaboradores=usuario)  # una sola fila por expediente: no hay duplicados
    return Expediente.objects.none()


def facturas_visibles(usuario):
    """Queryset de facturas que el usuario puede ver (las de sus expedientes; quien ve todo, todas)."""
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
