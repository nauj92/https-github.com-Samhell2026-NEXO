from django.db.models import Q
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from core.permisos import es_directivo, expedientes_visibles

from .models import Liquidacion
from .serializers import CalcularSerializer, LiquidacionSerializer, calcular_liquidacion


class LiquidacionViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Liquidaciones guardadas. `POST calcular/` calcula sin guardar."""

    serializer_class = LiquidacionSerializer

    def get_queryset(self):
        qs = Liquidacion.objects.select_related("expediente", "creado_por")
        usuario = self.request.user
        if es_directivo(usuario):
            return qs
        return qs.filter(Q(creado_por=usuario) | Q(expediente__in=expedientes_visibles(usuario)))

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)

    def perform_destroy(self, instance):
        usuario = self.request.user
        if not (es_directivo(usuario) or instance.creado_por_id == usuario.pk):
            raise PermissionDenied("Solo quien creó la liquidación o un directivo puede eliminarla.")
        instance.delete()

    @action(detail=False, methods=["post"], url_path="calcular")
    def calcular(self, request):
        entrada = CalcularSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        datos, resultado = calcular_liquidacion(entrada.validated_data["tipo"], entrada.validated_data["datos"])
        return Response({"tipo": entrada.validated_data["tipo"], "datos": datos, "resultado": resultado}, status=status.HTTP_200_OK)
