import os
from urllib.parse import quote

from django.http import HttpResponse
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.generics import ListAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permisos import ROL_CLIENTE, AccesoCompleto
from expedientes import almacenamiento, eventos
from expedientes.models import DocumentoExpediente, Expediente
from expedientes.serializers import DocumentoExpedienteSerializer
from facturacion.models import Factura
from notificaciones import servicios as avisos

from .models import Mensaje
from .serializers import ExpedientePortalSerializer, FacturaPortalSerializer, MensajeSerializer


class EsClienteConPortal(BasePermission):
    """Solo usuarios con rol Cliente vinculados a una ficha de cliente."""

    message = "Su cuenta de cliente aún no está vinculada a un cliente. Pida al despacho que la vincule."

    def has_permission(self, request, view):
        usuario = request.user
        return bool(getattr(usuario, "rol", None) == ROL_CLIENTE and getattr(usuario, "cliente_id", None))


class VistaPortal:
    acceso_cliente = True
    permission_classes = [AccesoCompleto, EsClienteConPortal]

    def expedientes(self):
        return Expediente.objects.filter(cliente_id=self.request.user.cliente_id)

    def expediente(self, pk):
        try:
            return self.expedientes().get(pk=pk)
        except Expediente.DoesNotExist:
            raise NotFound("El proceso no existe.")


class MisExpedientes(VistaPortal, ListAPIView):
    serializer_class = ExpedientePortalSerializer

    def get_queryset(self):
        return self.expedientes().select_related("juzgado", "abogado_asignado").prefetch_related("etapas", "audiencias")


class MisFacturas(VistaPortal, ListAPIView):
    serializer_class = FacturaPortalSerializer

    def get_queryset(self):
        return Factura.objects.filter(cliente_id=self.request.user.cliente_id).exclude(estado=Factura.Estado.ANULADA)


class MisDocumentos(VistaPortal, APIView):
    """GET lista los documentos compartidos con el cliente; POST (campo 'archivo') sube uno al despacho."""

    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, pk):
        expediente = self.expediente(pk)
        docs = expediente.documentos.filter(compartido_cliente=True).select_related("subido_por").defer("contenido")
        return Response(DocumentoExpedienteSerializer(docs, many=True).data)

    def post(self, request, pk):
        expediente = self.expediente(pk)
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
                ruta_externa = almacenamiento.guardar(expediente.pk, nombre, datos, tipo)
            except almacenamiento.ErrorAlmacenamiento as exc:
                return Response({"detail": f"{exc} Intente de nuevo."}, status=status.HTTP_502_BAD_GATEWAY)
        try:
            doc = DocumentoExpediente.objects.create(
                expediente=expediente, nombre=nombre[:255], tipo_contenido=tipo, tamano=archivo.size,
                contenido=b"" if ruta_externa else datos, ruta_externa=ruta_externa, subido_por=request.user,
                compartido_cliente=True, origen_cliente=True,
            )
        except Exception:
            if ruta_externa:
                almacenamiento.borrar(ruta_externa)
            raise
        eventos.registrar(expediente, request.user, "Documento adjuntado por el cliente", [("Documento", "—", doc.nombre)])
        avisos.notificar_despacho_del_cliente(
            expediente, f"El cliente subió «{doc.nombre}» en el proceso {expediente.numero}", f"portal:doc:{doc.pk}"
        )
        return Response(DocumentoExpedienteSerializer(doc).data, status=status.HTTP_201_CREATED)


class DescargarDocumento(VistaPortal, APIView):
    def get(self, request, pk, doc_id):
        expediente = self.expediente(pk)
        try:
            doc = expediente.documentos.get(pk=doc_id, compartido_cliente=True)
        except DocumentoExpediente.DoesNotExist:
            raise NotFound("El documento no existe.")
        try:
            contenido = doc.leer_contenido()
        except almacenamiento.ErrorAlmacenamiento as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        respuesta = HttpResponse(contenido, content_type="application/octet-stream")
        respuesta["Content-Disposition"] = f"attachment; filename*=UTF-8''{quote(doc.nombre)}"
        respuesta["X-Content-Type-Options"] = "nosniff"
        return respuesta


class MisMensajes(VistaPortal, APIView):
    """GET lista la conversación del proceso; POST {"texto"} escribe al despacho."""

    def get(self, request, pk):
        expediente = self.expediente(pk)
        return Response(MensajeSerializer(expediente.mensajes.select_related("autor"), many=True).data)

    def post(self, request, pk):
        expediente = self.expediente(pk)
        serializer = MensajeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mensaje = serializer.save(expediente=expediente, autor=request.user, de_cliente=True)
        avisos.notificar_despacho_del_cliente(
            expediente, f"Mensaje del cliente en el proceso {expediente.numero}: {mensaje.texto[:120]}",
            f"portal:msg:{mensaje.pk}",
        )
        return Response(MensajeSerializer(mensaje).data, status=status.HTTP_201_CREATED)


class MensajesDespacho(APIView):
    """Conversación con el cliente vista por el personal. GET ?expediente=ID; POST {"expediente", "texto"}."""

    modulo = "expedientes"
    permisos_accion = {}
    permission_classes = [AccesoCompleto]

    def _expediente(self, request, pk):
        from core.permisos import expedientes_visibles

        try:
            return expedientes_visibles(request.user).get(pk=pk)
        except (Expediente.DoesNotExist, ValueError, TypeError):
            raise NotFound("El expediente no existe.")

    def get(self, request):
        expediente = self._expediente(request, request.query_params.get("expediente"))
        return Response(MensajeSerializer(expediente.mensajes.select_related("autor"), many=True).data)

    def post(self, request):
        expediente = self._expediente(request, request.data.get("expediente"))
        if expediente.cliente_id is None:
            return Response({"detail": "El expediente no tiene cliente asignado."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = MensajeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mensaje = serializer.save(expediente=expediente, autor=request.user, de_cliente=False)
        avisos.notificar_cliente(
            expediente.cliente, f"Nuevo mensaje en su proceso {expediente.numero}",
            f"El despacho le escribió en el proceso {expediente.numero}: {mensaje.texto[:200]}",
            f"portal:msg:{mensaje.pk}",
        )
        return Response(MensajeSerializer(mensaje).data, status=status.HTTP_201_CREATED)
