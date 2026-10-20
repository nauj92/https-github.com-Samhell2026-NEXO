import logging

from rest_framework import viewsets

from .models import Notificacion
from .serializers import NotificacionSerializer
from .servicios import generar_para_usuario

logger = logging.getLogger(__name__)


class NotificacionViewSet(viewsets.ModelViewSet):
    serializer_class = NotificacionSerializer

    def get_queryset(self):
        return Notificacion.objects.filter(usuario=self.request.user)

    def list(self, request, *args, **kwargs):
        # Antes de listar, se generan los avisos pendientes (audiencias, plazos, facturas).
        # Un fallo aquí nunca debe impedir que el usuario vea sus notificaciones.
        try:
            generar_para_usuario(request.user)
        except Exception:
            logger.exception("Falló la generación automática de notificaciones")
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)
