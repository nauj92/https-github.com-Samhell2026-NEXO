from rest_framework import viewsets

from core.permisos import EsDirectivo

from .models import Cliente
from .serializers import ClienteSerializer


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer

    def get_permissions(self):
        # Cualquier usuario autenticado puede crear y editar clientes; borrarlos es de directivos.
        if self.action == "destroy":
            return [EsDirectivo()]
        return super().get_permissions()
