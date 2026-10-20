from rest_framework import viewsets

from core.permisos import facturas_visibles

from .serializers import FacturaSerializer


class FacturaViewSet(viewsets.ModelViewSet):
    serializer_class = FacturaSerializer

    def get_queryset(self):
        return facturas_visibles(self.request.user).select_related("cliente", "expediente")
