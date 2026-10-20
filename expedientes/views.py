import os
from datetime import timedelta
from urllib.parse import quote

from django.db.models import Count, Q, Sum
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from simple_history.models import HistoricalRecords

from audiencias.models import Audiencia
from core.permisos import EsDirectivo, es_directivo, expedientes_visibles, facturas_visibles
from facturacion.models import Factura

from .historial import historial_de
from .models import DocumentoExpediente, EtapaProceso, Expediente, Juzgado
from .serializers import (
    DocumentoExpedienteSerializer,
    EtapaProcesoSerializer,
    ExpedienteSerializer,
    JuzgadoSerializer,
)


class EliminarProtegidoMixin:
    """Responde con un mensaje claro (409) si el registro no se puede borrar por tener datos asociados."""

    mensaje_protegido = "No se puede eliminar porque tiene registros asociados."

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response({"detail": self.mensaje_protegido}, status=status.HTTP_409_CONFLICT)


class JuzgadoViewSet(EliminarProtegidoMixin, viewsets.ModelViewSet):
    queryset = Juzgado.objects.all().order_by("nombre")
    serializer_class = JuzgadoSerializer
    mensaje_protegido = "No se puede eliminar el juzgado porque tiene expedientes asociados."

    def get_permissions(self):
        # Cualquier usuario autenticado puede crear juzgados; editarlos o borrarlos es de directivos.
        if self.action in ("update", "partial_update", "destroy"):
            return [EsDirectivo()]
        return super().get_permissions()


class ExpedienteViewSet(EliminarProtegidoMixin, viewsets.ModelViewSet):
    serializer_class = ExpedienteSerializer
    mensaje_protegido = (
        "No se puede eliminar el expediente porque tiene facturas asociadas. "
        "Elimine o reasigne primero las facturas."
    )

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        # simple_history toma al autor del cambio de la petición. Con JWT, el
        # middleware de Django no conoce al usuario, así que se lo indicamos aquí.
        try:
            HistoricalRecords.context.request = request
        except AttributeError:  # versión de simple_history sin este mecanismo: el historial queda sin autor
            pass

    def get_queryset(self):
        return (
            expedientes_visibles(self.request.user)
            .select_related("juzgado", "cliente", "abogado_asignado")
            .prefetch_related("etapas")
        )

    def perform_create(self, serializer):
        # Si no se especifica abogado_asignado, se asigna al usuario que crea el expediente
        if not serializer.validated_data.get("abogado_asignado"):
            serializer.save(abogado_asignado=self.request.user)
        else:
            serializer.save()

    def perform_update(self, serializer):
        serializer.instance._history_user = self.request.user
        serializer.save()

    def perform_destroy(self, instance):
        instance._history_user = self.request.user
        instance.delete()

    # ---- Historial de cambios -------------------------------------------------
    @action(detail=True, methods=["get"])
    def historial(self, request, pk=None):
        """GET /api/expedientes/{id}/historial/ -> quién cambió qué y cuándo."""
        return Response(historial_de(self.get_object()))

    # ---- Documentos adjuntos --------------------------------------------------
    @action(detail=True, methods=["get", "post"], url_path="documentos", parser_classes=[MultiPartParser, FormParser])
    def documentos(self, request, pk=None):
        """GET lista los documentos del expediente; POST (campo 'archivo') sube uno nuevo."""
        expediente = self.get_object()

        if request.method == "GET":
            docs = expediente.documentos.select_related("subido_por").defer("contenido")
            return Response(DocumentoExpedienteSerializer(docs, many=True).data)

        archivo = request.FILES.get("archivo")
        if archivo is None:
            return Response({"detail": "Seleccione un archivo para subir."}, status=status.HTTP_400_BAD_REQUEST)
        if archivo.size == 0:
            return Response({"detail": "El archivo está vacío."}, status=status.HTTP_400_BAD_REQUEST)
        if archivo.size > DocumentoExpediente.TAMANO_MAXIMO:
            limite = DocumentoExpediente.TAMANO_MAXIMO // (1024 * 1024)
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

        doc = DocumentoExpediente.objects.create(
            expediente=expediente,
            nombre=nombre[:255],
            tipo_contenido=(archivo.content_type or "")[:100],
            tamano=archivo.size,
            contenido=archivo.read(),
            subido_por=request.user,
        )
        return Response(DocumentoExpedienteSerializer(doc).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get", "delete"], url_path=r"documentos/(?P<doc_id>[0-9]+)")
    def documento(self, request, pk=None, doc_id=None):
        """GET descarga el documento; DELETE lo elimina."""
        expediente = self.get_object()
        try:
            doc = expediente.documentos.get(pk=doc_id)
        except DocumentoExpediente.DoesNotExist:
            raise NotFound("El documento no existe.")

        if request.method == "DELETE":
            if not es_directivo(request.user) and doc.subido_por_id != request.user.id:
                return Response(
                    {"detail": "Solo quien subió el documento, un socio o un administrador puede eliminarlo."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            doc.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        respuesta = HttpResponse(bytes(doc.contenido), content_type="application/octet-stream")
        respuesta["Content-Disposition"] = f"attachment; filename*=UTF-8''{quote(doc.nombre)}"
        respuesta["X-Content-Type-Options"] = "nosniff"
        return respuesta


class EtapaProcesoViewSet(viewsets.ModelViewSet):
    serializer_class = EtapaProcesoSerializer

    def get_queryset(self):
        return EtapaProceso.objects.filter(expediente__in=expedientes_visibles(self.request.user))


class DashboardStatsView(APIView):
    def get(self, request):
        hoy = timezone.localdate()
        en_7_dias = hoy + timedelta(days=7)

        expedientes = expedientes_visibles(request.user)
        conteo = expedientes.aggregate(
            activos=Count("id", filter=Q(estado=Expediente.Estado.ACTIVO)),
            tramite=Count("id", filter=Q(estado=Expediente.Estado.TRAMITE)),
            cerrados=Count("id", filter=Q(estado=Expediente.Estado.CERRADO)),
        )

        audiencias = Audiencia.objects.filter(expediente__in=expedientes)
        audiencias_pendientes = audiencias.filter(fecha_hora__date__gte=hoy, fecha_hora__date__lte=en_7_dias).count()
        audiencias_hoy = audiencias.filter(fecha_hora__date=hoy).count()

        # Plazos que requieren atención: etapas sin completar que vencen en 7 días o ya vencieron
        etapas = EtapaProceso.objects.filter(expediente__in=expedientes, fecha_limite__isnull=False).exclude(
            estado=EtapaProceso.Estado.COMPLETADA
        )
        plazos_procesales = etapas.filter(fecha_limite__lte=en_7_dias).count()
        plazos_vencidos = etapas.filter(fecha_limite__lt=hoy).count()

        # Ingresos del mes = facturas PAGADAS en el mes (por fecha de pago; si no la tienen, por emisión)
        facturas = facturas_visibles(request.user)
        ingresos_mes = (
            facturas.filter(estado=Factura.Estado.PAGADA)
            .filter(
                Q(fecha_pago__year=hoy.year, fecha_pago__month=hoy.month)
                | Q(fecha_pago__isnull=True, fecha_emision__year=hoy.year, fecha_emision__month=hoy.month)
            )
            .aggregate(total=Sum("monto"))["total"]
            or 0
        )
        por_cobrar = (
            facturas.filter(estado__in=[Factura.Estado.PENDIENTE, Factura.Estado.VENCIDA]).aggregate(
                total=Sum("monto")
            )["total"]
            or 0
        )

        casos_por_materia = list(expedientes.values("materia").annotate(total=Count("id")).order_by("-total"))

        return Response(
            {
                "casos_activos": conteo["activos"],
                "casos_tramite": conteo["tramite"],
                "casos_cerrados": conteo["cerrados"],
                "audiencias_pendientes": audiencias_pendientes,
                "audiencias_hoy": audiencias_hoy,
                "plazos_procesales": plazos_procesales,
                "plazos_vencidos": plazos_vencidos,
                "ingresos_mes": ingresos_mes,
                "por_cobrar": por_cobrar,
                "casos_por_materia": casos_por_materia,
            }
        )
