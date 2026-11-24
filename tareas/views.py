import os
from urllib.parse import quote

from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from core.permisos import MENSAJE_SIN_PERMISO, puede
from expedientes import almacenamiento, eventos
from expedientes.models import DocumentoExpediente
from notificaciones import servicios as avisos

from .alcance import tareas_visibles
from .models import ComprobanteTarea, Tarea
from .serializers import TareaSerializer


class TareaViewSet(viewsets.ModelViewSet):
    """Tareas y trámites. Cada quien ve las suyas (asignadas a él o creadas por él); quien ve todo el despacho, todas.

    Quien puede crear (administrador, abogado, secretaria) además ve las tareas de los expedientes que le
    corresponden. El escribiente y el dependiente solo ven las que les asignaron.
    """

    serializer_class = TareaSerializer
    modulo = "tareas"
    permisos_accion = {
        # Los comprobantes se suben con el permiso de «documentos»; verlos, con el de «tareas»
        "comprobantes": {"GET": "V", "POST": ("documentos", "C")},
        "comprobante": {"GET": "V", "DELETE": "E"},
    }

    def get_queryset(self):
        usuario = self.request.user
        qs = tareas_visibles(usuario).select_related("expediente", "asignado_a", "creado_por").prefetch_related(
            "comprobantes__subido_por"
        )
        params = self.request.query_params
        if params.get("estado") in Tarea.Estado.values:
            qs = qs.filter(estado=params["estado"])
        if params.get("mias") in ("1", "true"):
            qs = qs.filter(asignado_a=usuario)
        if params.get("expediente", "").isdigit():
            qs = qs.filter(expediente_id=params["expediente"])
        return qs.distinct()

    @transaction.atomic
    def perform_create(self, serializer):
        tarea = serializer.save(creado_por=self.request.user)
        if tarea.expediente:
            eventos.registrar(
                tarea.expediente, self.request.user, "Tarea asignada",
                [("Tarea", "—", f"{tarea.titulo} → {serializer._nombre(tarea.asignado_a) or 'sin asignar'}")],
            )
        avisos.notificar_tarea_asignada(tarea, self.request.user)

    @transaction.atomic
    def perform_update(self, serializer):
        usuario = self.request.user
        anterior = serializer.instance
        if not puede(usuario, "tareas", "C") and anterior.asignado_a_id != usuario.pk:
            raise PermissionDenied(MENSAJE_SIN_PERMISO)
        asignado_antes, estado_antes = anterior.asignado_a_id, anterior.estado
        tarea = serializer.save()
        if tarea.estado != estado_antes:
            tarea.fecha_realizada = timezone.now() if tarea.estado == Tarea.Estado.REALIZADA else None
            tarea.save(update_fields=["fecha_realizada"])
            if tarea.expediente:
                nombres = dict(Tarea.Estado.choices)
                eventos.registrar(
                    tarea.expediente, usuario, "Tarea actualizada",
                    [(f"Tarea «{tarea.titulo}» · Estado", nombres[estado_antes], nombres[tarea.estado])],
                )
            if tarea.estado == Tarea.Estado.REALIZADA:
                avisos.notificar_tarea_realizada(tarea, usuario)
        if tarea.asignado_a_id != asignado_antes:
            avisos.notificar_tarea_asignada(tarea, usuario)

    # ---- Comprobantes ---------------------------------------------------------
    @action(detail=True, methods=["get", "post"], url_path="comprobantes", parser_classes=[MultiPartParser, FormParser])
    def comprobantes(self, request, pk=None):
        """GET lista los comprobantes de la tarea; POST (campo 'archivo') sube uno."""
        tarea = self.get_object()
        if request.method == "GET":
            return Response(TareaSerializer(tarea, context={"request": request}).data["comprobantes"])

        if not puede(request.user, "tareas", "C") and tarea.asignado_a_id != request.user.pk:
            raise PermissionDenied(MENSAJE_SIN_PERMISO)
        archivo = request.FILES.get("archivo")
        if archivo is None:
            return Response({"detail": "Seleccione un archivo para subir."}, status=status.HTTP_400_BAD_REQUEST)
        if archivo.size == 0:
            return Response({"detail": "El archivo está vacío."}, status=status.HTTP_400_BAD_REQUEST)
        if archivo.size > DocumentoExpediente.limite():
            limite = DocumentoExpediente.limite() // (1024 * 1024)
            return Response(
                {"detail": f"El archivo supera el tamaño máximo permitido ({limite} MB)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        nombre = os.path.basename(archivo.name)
        extension = os.path.splitext(nombre)[1].lower().lstrip(".")
        if extension not in DocumentoExpediente.EXTENSIONES_PERMITIDAS:
            permitidas = ", ".join(DocumentoExpediente.EXTENSIONES_PERMITIDAS)
            return Response(
                {"detail": f"Tipo de archivo no permitido. Formatos aceptados: {permitidas}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        datos = archivo.read()
        tipo = (archivo.content_type or "")[:100]
        ruta_externa = ""
        if almacenamiento.configurado():
            try:
                ruta_externa = almacenamiento.guardar(tarea.pk, nombre, datos, tipo, carpeta="tareas")
            except almacenamiento.ErrorAlmacenamiento as exc:
                return Response({"detail": f"{exc} Intente de nuevo."}, status=status.HTTP_502_BAD_GATEWAY)
        try:
            comprobante = ComprobanteTarea.objects.create(
                tarea=tarea,
                nombre=nombre[:255],
                tipo_contenido=tipo,
                tamano=archivo.size,
                contenido=b"" if ruta_externa else datos,
                ruta_externa=ruta_externa,
                subido_por=request.user,
            )
        except Exception:
            if ruta_externa:
                almacenamiento.borrar(ruta_externa)
            raise
        if tarea.expediente:
            eventos.registrar(
                tarea.expediente, request.user, "Comprobante de tarea adjuntado",
                [(f"Tarea «{tarea.titulo}»", "—", comprobante.nombre)],
            )
        tarea = self.get_queryset().get(pk=tarea.pk)  # recarga: la copia anterior trae los comprobantes en caché
        return Response(TareaSerializer(tarea, context={"request": request}).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get", "delete"], url_path=r"comprobantes/(?P<comprobante_id>[0-9]+)")
    def comprobante(self, request, pk=None, comprobante_id=None):
        """GET descarga el comprobante; DELETE lo elimina (quien lo subió o quien crea tareas)."""
        tarea = self.get_object()
        try:
            comprobante = tarea.comprobantes.get(pk=comprobante_id)
        except ComprobanteTarea.DoesNotExist:
            return Response({"detail": "Comprobante no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        if request.method == "DELETE":
            if not puede(request.user, "tareas", "C") and comprobante.subido_por_id != request.user.pk:
                raise PermissionDenied(MENSAJE_SIN_PERMISO)
            nombre = comprobante.nombre
            comprobante.delete()
            if tarea.expediente:
                eventos.registrar(
                    tarea.expediente, request.user, "Comprobante de tarea eliminado",
                    [(f"Tarea «{tarea.titulo}»", nombre, "—")],
                )
            return Response(status=status.HTTP_204_NO_CONTENT)

        try:
            contenido = comprobante.leer_contenido()
        except almacenamiento.ErrorAlmacenamiento as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        respuesta = HttpResponse(contenido, content_type=comprobante.tipo_contenido or "application/octet-stream")
        respuesta["Content-Disposition"] = f"attachment; filename*=UTF-8''{quote(comprobante.nombre)}"
        return respuesta
