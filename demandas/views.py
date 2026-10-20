from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from core.permisos import es_directivo, expedientes_visibles

from .models import Citacion, ContestacionDemanda, Demanda
from .plantillas import borrador_contestacion, borrador_demanda
from .serializers import CitacionSerializer, ContestacionSerializer, DemandaSerializer


class AlcanceAbogadoMixin:
    """Cada abogado ve lo que tiene a su cargo o lo de sus expedientes; administrador y socio ven todo."""

    relaciones = ()

    def get_queryset(self):
        qs = self.queryset_base().select_related(*self.relaciones)
        usuario = self.request.user
        if es_directivo(usuario):
            return qs
        return qs.filter(Q(abogado_responsable=usuario) | Q(expediente__in=expedientes_visibles(usuario)))

    def perform_create(self, serializer):
        # Si no se indica responsable, queda a cargo de quien lo registra
        if serializer.validated_data.get("abogado_responsable") is None:
            serializer.save(abogado_responsable=self.request.user)
        else:
            serializer.save()

    def perform_destroy(self, instance):
        usuario = self.request.user
        if not (es_directivo(usuario) or instance.abogado_responsable_id == usuario.pk):
            raise PermissionDenied("Solo el abogado responsable o un directivo puede eliminarlo.")
        instance.delete()


class DemandaViewSet(AlcanceAbogadoMixin, viewsets.ModelViewSet):
    serializer_class = DemandaSerializer
    relaciones = ("cliente", "expediente", "juzgado", "abogado_responsable")

    def queryset_base(self):
        return Demanda.objects.all()

    @action(detail=True, methods=["get"], url_path="generar-borrador")
    def generar_borrador(self, request, pk=None):
        """Texto base del escrito de demanda con los datos registrados (no lo guarda)."""
        return Response({"borrador": borrador_demanda(self.get_object())})


class ContestacionViewSet(AlcanceAbogadoMixin, viewsets.ModelViewSet):
    serializer_class = ContestacionSerializer
    relaciones = ("cliente", "expediente", "juzgado", "abogado_responsable")

    def queryset_base(self):
        return ContestacionDemanda.objects.all()

    @action(detail=True, methods=["get"], url_path="generar-borrador")
    def generar_borrador(self, request, pk=None):
        return Response({"borrador": borrador_contestacion(self.get_object())})


class CitacionViewSet(AlcanceAbogadoMixin, viewsets.ModelViewSet):
    serializer_class = CitacionSerializer
    relaciones = ("demanda", "expediente", "abogado_responsable")

    def queryset_base(self):
        return Citacion.objects.all()
