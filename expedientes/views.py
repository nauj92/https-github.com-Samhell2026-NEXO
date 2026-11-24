import os
from datetime import timedelta
from urllib.parse import quote

from django.db.models import Count, Q, Sum
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from simple_history.models import HistoricalRecords

from audiencias.models import Audiencia
from core.permisos import (
    ROL_ABOGADO, ROL_SECRETARIA, EsAdministrador, expedientes_visibles, facturas_visibles, permiso_de,
)
from facturacion.models import Factura
from notificaciones import servicios as avisos

from .historial import historial_de
from . import almacenamiento, eventos
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
        # Todo el personal consulta el catálogo; crear juzgados lo hace quien puede crear expedientes;
        # editarlos o borrarlos es del administrador.
        if self.action == "create":
            return [permiso_de("expedientes", "C")()]
        if self.action in ("update", "partial_update", "destroy"):
            return [EsAdministrador()]
        return super().get_permissions()


class ExpedienteViewSet(EliminarProtegidoMixin, viewsets.ModelViewSet):
    serializer_class = ExpedienteSerializer
    modulo = "expedientes"
    # Los documentos adjuntos pertenecen al módulo «documentos» de la matriz de permisos
    permisos_accion = {
        "documentos": {"GET": ("documentos", "V"), "POST": ("documentos", "C")},
        "documento": {"GET": ("documentos", "V"), "DELETE": ("documentos", "X")},
        # Compartir con el cliente es una decisión del abogado (letra «A» de documentos)
        "compartir_documento": ("documentos", "A"),
    }
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
        usuario = self.request.user
        datos = {}
        if not serializer.validated_data.get("abogado_asignado"):
            # Un abogado que crea el expediente queda como responsable; los demás deben indicar el abogado.
            if usuario.rol != ROL_ABOGADO:
                raise ValidationError({"abogado_asignado": "Indique el abogado responsable del expediente."})
            datos["abogado_asignado"] = usuario
        if usuario.rol == ROL_SECRETARIA and not usuario.is_superuser:
            # La secretaria que da de alta un expediente queda en su equipo de apoyo para poder seguir viéndolo
            datos["colaboradores"] = [usuario]
        serializer.save(**datos)

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
                expediente=expediente,
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
        eventos.registrar(expediente, request.user, "Documento adjuntado", [("Documento", "—", doc.nombre)])
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
            eventos.registrar(expediente, request.user, "Documento eliminado", [("Documento", doc.nombre, "—")])
            doc.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        try:
            contenido = doc.leer_contenido()
        except almacenamiento.ErrorAlmacenamiento as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        respuesta = HttpResponse(contenido, content_type="application/octet-stream")
        respuesta["Content-Disposition"] = f"attachment; filename*=UTF-8''{quote(doc.nombre)}"
        respuesta["X-Content-Type-Options"] = "nosniff"
        return respuesta


    @action(detail=True, methods=["post"], url_path=r"documentos/(?P<doc_id>[0-9]+)/compartir")
    def compartir_documento(self, request, pk=None, doc_id=None):
        """POST {"compartido": true|false}: publica u oculta el documento en el portal del cliente."""
        expediente = self.get_object()
        try:
            doc = expediente.documentos.get(pk=doc_id)
        except DocumentoExpediente.DoesNotExist:
            raise NotFound("El documento no existe.")
        compartir = request.data.get("compartido") in (True, "true", "True", "1", 1)
        if compartir and expediente.cliente_id is None:
            raise ValidationError({"detail": "El expediente no tiene cliente asignado."})
        if doc.compartido_cliente != compartir:
            doc.compartido_cliente = compartir
            doc.save(update_fields=["compartido_cliente"])
            eventos.registrar(
                expediente, request.user,
                "Documento compartido con el cliente" if compartir else "Documento ocultado al cliente",
                [("Documento", "—", doc.nombre)],
            )
            if compartir:
                avisos.notificar_cliente(
                    expediente.cliente, f"Nuevo documento en su proceso {expediente.numero}",
                    f"El despacho compartió el documento «{doc.nombre}» en su proceso {expediente.numero}.",
                    f"documento:{doc.pk}:compartido",
                )
        return Response(DocumentoExpedienteSerializer(doc).data)


class EtapaProcesoViewSet(viewsets.ModelViewSet):
    serializer_class = EtapaProcesoSerializer
    modulo = "agenda"  # las etapas con fecha límite son los plazos de la agenda

    def get_queryset(self):
        return EtapaProceso.objects.filter(expediente__in=expedientes_visibles(self.request.user))

    # Cada cambio en las etapas queda en el historial del expediente
    def perform_create(self, serializer):
        etapa = serializer.save()
        eventos.registrar(etapa.expediente, self.request.user, "Etapa agregada", [("Etapa", "—", eventos.texto_etapa(etapa))])

    def perform_update(self, serializer):
        antes = eventos.instantanea_etapa(serializer.instance)
        etapa = serializer.save()
        cambios = eventos.cambios_de_etapa(antes, etapa)
        if cambios:
            eventos.registrar(etapa.expediente, self.request.user, "Etapa modificada", cambios)

    def perform_destroy(self, instance):
        eventos.registrar(instance.expediente, self.request.user, "Etapa eliminada", [("Etapa", eventos.texto_etapa(instance), "—")])
        instance.delete()


class DashboardStatsView(APIView):
    modulo = "reportes"

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
