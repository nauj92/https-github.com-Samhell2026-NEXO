from rest_framework import viewsets
from .models import Audiencia
from .serializers import AudienciaSerializer


class AudienciaViewSet(viewsets.ModelViewSet):
    queryset = Audiencia.objects.all()
    serializer_class = AudienciaSerializer