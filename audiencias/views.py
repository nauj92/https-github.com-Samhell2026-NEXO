from rest_framework import viewsets

from core.permisos import expedientes_visibles

from .models import Audiencia
from .serializers import AudienciaSerializer


class AudienciaViewSet(viewsets.ModelViewSet):
    serializer_class = AudienciaSerializer

    def get_queryset(self):
        return Audiencia.objects.filter(expediente__in=expedientes_visibles(self.request.user)).select_related(
            "expediente__juzgado", "expediente__abogado_asignado"
        )
