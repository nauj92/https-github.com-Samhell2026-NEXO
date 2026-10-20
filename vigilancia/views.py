from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permisos import expedientes_visibles

from .models import ActuacionVigilancia, EnlaceVigilancia, Vigilancia
from .serializers import ActuacionSerializer, EnlaceSerializer, VigilanciaSerializer


class VigilanciaViewSet(viewsets.ModelViewSet):
    serializer_class = VigilanciaSerializer

    def get_queryset(self):
        return (
            Vigilancia.objects.filter(expediente__in=expedientes_visibles(self.request.user))
            .select_related("expediente__juzgado")
            .prefetch_related("actuaciones", "enlaces")
        )

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)

    @action(detail=True, methods=["get", "post"], url_path="actuaciones")
    def actuaciones(self, request, pk=None):
        """GET lista las actuaciones; POST registra una nueva."""
        vigilancia = self.get_object()
        if request.method == "GET":
            return Response(ActuacionSerializer(vigilancia.actuaciones.select_related("registrada_por"), many=True).data)
        serializer = ActuacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            serializer.save(vigilancia=vigilancia, registrada_por=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path=r"actuaciones/(?P<act_id>[0-9]+)")
    def actuacion(self, request, pk=None, act_id=None):
        vigilancia = self.get_object()
        try:
            actuacion = vigilancia.actuaciones.get(pk=act_id)
        except ActuacionVigilancia.DoesNotExist:
            return Response({"detail": "La actuación no existe."}, status=status.HTTP_404_NOT_FOUND)
        actuacion.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get", "post"], url_path="enlaces")
    def enlaces(self, request, pk=None):
        """GET lista los enlaces anclados al proceso; POST ancla uno nuevo."""
        vigilancia = self.get_object()
        if request.method == "GET":
            return Response(EnlaceSerializer(vigilancia.enlaces.select_related("creado_por"), many=True).data)
        serializer = EnlaceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(vigilancia=vigilancia, creado_por=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path=r"enlace/(?P<enlace_id>[0-9]+)")
    def enlace(self, request, pk=None, enlace_id=None):
        vigilancia = self.get_object()
        try:
            enlace = vigilancia.enlaces.get(pk=enlace_id)
        except EnlaceVigilancia.DoesNotExist:
            return Response({"detail": "El enlace no existe."}, status=status.HTTP_404_NOT_FOUND)
        enlace.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
