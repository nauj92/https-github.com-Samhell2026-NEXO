from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count
from .models import Juzgado, Expediente, EtapaProceso
from .serializers import JuzgadoSerializer, ExpedienteSerializer, EtapaProcesoSerializer
from audiencias.models import Audiencia
from facturacion.models import Factura


class JuzgadoViewSet(viewsets.ModelViewSet):
    queryset = Juzgado.objects.all()
    serializer_class = JuzgadoSerializer


class ExpedienteViewSet(viewsets.ModelViewSet):
    serializer_class = ExpedienteSerializer

    def get_queryset(self):
        usuario = self.request.user
        if usuario.rol in ["administrador", "socio_director"]:
            return Expediente.objects.all()
        # Abogados y secretarios solo ven los expedientes que tienen asignados
        return Expediente.objects.filter(abogado_asignado=usuario)

    def perform_create(self, serializer):
        # Si no se especifica abogado_asignado, se asigna automáticamente al usuario que crea el expediente
        if not serializer.validated_data.get("abogado_asignado"):
            serializer.save(abogado_asignado=self.request.user)
        else:
            serializer.save()


class EtapaProcesoViewSet(viewsets.ModelViewSet):
    queryset = EtapaProceso.objects.all()
    serializer_class = EtapaProcesoSerializer


class DashboardStatsView(APIView):
    def get(self, request):
        hoy = timezone.now().date()
        en_7_dias = hoy + timedelta(days=7)

        casos_activos = Expediente.objects.filter(estado=Expediente.Estado.ACTIVO).count()
        casos_tramite = Expediente.objects.filter(estado=Expediente.Estado.TRAMITE).count()
        casos_cerrados = Expediente.objects.filter(estado=Expediente.Estado.CERRADO).count()

        audiencias_pendientes = Audiencia.objects.filter(
            fecha_hora__date__gte=hoy, fecha_hora__date__lte=en_7_dias
        ).count()
        audiencias_hoy = Audiencia.objects.filter(fecha_hora__date=hoy).count()

        plazos_procesales = EtapaProceso.objects.filter(
            estado=EtapaProceso.Estado.PENDIENTE, fecha_limite__isnull=False
        ).count()

        ingresos_mes = Factura.objects.filter(
            fecha_emision__year=hoy.year, fecha_emision__month=hoy.month
        ).aggregate(total=Sum("monto"))["total"] or 0

        casos_por_materia = list(
            Expediente.objects.values("materia").annotate(total=Count("id")).order_by("-total")
        )

        data = {
            "casos_activos": casos_activos,
            "casos_tramite": casos_tramite,
            "casos_cerrados": casos_cerrados,
            "audiencias_pendientes": audiencias_pendientes,
            "audiencias_hoy": audiencias_hoy,
            "plazos_procesales": plazos_procesales,
            "ingresos_mes": ingresos_mes,
            "casos_por_materia": casos_por_materia,
        }
        return Response(data)