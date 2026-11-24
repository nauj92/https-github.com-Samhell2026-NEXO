from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from core.permisos import MENSAJE_SIN_PERMISO, es_directivo, expedientes_visibles, puede
from notificaciones import servicios as avisos

from .models import Citacion, ContestacionDemanda, Demanda
from .plantillas import borrador_contestacion, borrador_demanda
from .serializers import CitacionSerializer, ContestacionSerializer, DemandaSerializer


class AlcanceAbogadoMixin:
    """Cada abogado ve lo que tiene a su cargo o lo de sus expedientes; administrador y socio ven todo."""

    relaciones = ()
    modulo = "documentos"  # demandas, contestaciones y citaciones son escritos del despacho
    # Enviar a aprobación lo puede quien edita escritos; aprobar y devolver, solo quien tiene «A» (el abogado)
    permisos_accion = {"generar_borrador": "V", "enviar": "E", "aprobar": "A", "devolver": "A"}
    # Estados del escrito que solo se alcanzan con el escrito aprobado por el abogado (ver `_exigir_aprobado`)
    estados_con_aprobacion = ()
    etiqueta = "escrito"

    def get_queryset(self):
        qs = self.queryset_base().select_related(*self.relaciones)
        usuario = self.request.user
        if es_directivo(usuario):
            return qs
        return qs.filter(Q(abogado_responsable=usuario) | Q(expediente__in=expedientes_visibles(usuario)))

    def _exigir_aprobado(self, estado, aprobacion):
        if estado in self.estados_con_aprobacion and aprobacion != "aprobado":
            raise ValidationError({"estado": "El abogado debe aprobar el escrito antes de pasar a este estado."})

    def perform_create(self, serializer):
        # Lo que crea quien puede aprobar (el abogado) nace aprobado; lo demás nace como borrador
        usuario = self.request.user
        if not puede(usuario, "documentos", "E"):  # el dependiente solo sube comprobantes, no redacta escritos
            raise PermissionDenied(MENSAJE_SIN_PERMISO)
        extra = {}
        if puede(usuario, "documentos", "A"):
            extra = {"aprobacion": "aprobado", "aprobado_por": usuario, "aprobado_en": timezone.now()}
        self._exigir_aprobado(serializer.validated_data.get("estado"), extra.get("aprobacion", "borrador"))
        # Si no se indica responsable, queda a cargo de quien lo registra (si es abogado)
        if serializer.validated_data.get("abogado_responsable") is None:
            if usuario.rol != "abogado":
                raise ValidationError({"abogado_responsable": "Indique el abogado responsable."})
            serializer.save(abogado_responsable=usuario, **extra)
        else:
            serializer.save(**extra)

    def perform_update(self, serializer):
        usuario = self.request.user
        actual = serializer.instance
        extra = {}
        # Quien no puede aprobar y modifica un escrito pendiente o aprobado lo devuelve a borrador
        if not puede(usuario, "documentos", "A") and actual.aprobacion in ("aprobado", "pendiente"):
            extra = {"aprobacion": "borrador", "aprobado_por": None, "aprobado_en": None, "enviado_por": None}
        self._exigir_aprobado(
            serializer.validated_data.get("estado", actual.estado), extra.get("aprobacion", actual.aprobacion)
        )
        serializer.save(**extra)

    def _responder(self, instancia):
        return Response(self.get_serializer(self.get_queryset().get(pk=instancia.pk)).data)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def enviar(self, request, pk=None):
        """El escribiente o la secretaria envían el borrador a aprobación del abogado."""
        obj = self.get_object()
        if obj.aprobacion not in ("borrador", "devuelto"):
            raise ValidationError({"detail": "Solo se puede enviar a aprobación un borrador o un escrito devuelto."})
        obj.aprobacion, obj.enviado_por, obj.motivo_devolucion = "pendiente", request.user, ""
        obj.save(update_fields=["aprobacion", "enviado_por", "motivo_devolucion"])
        avisos.notificar_borrador_pendiente(obj, self.etiqueta, request.user)
        return self._responder(obj)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def aprobar(self, request, pk=None):
        """El abogado aprueba el escrito pendiente."""
        obj = self.get_object()
        if obj.aprobacion != "pendiente":
            raise ValidationError({"detail": "Solo se puede aprobar un escrito pendiente de aprobación."})
        obj.aprobacion, obj.aprobado_por, obj.aprobado_en, obj.motivo_devolucion = (
            "aprobado", request.user, timezone.now(), "",
        )
        obj.save(update_fields=["aprobacion", "aprobado_por", "aprobado_en", "motivo_devolucion"])
        avisos.notificar_borrador_resuelto(obj, self.etiqueta, request.user, aprobado=True)
        # Aviso externo: ya con el visto bueno del abogado, el cliente sabe que su proceso avanzó
        if obj.expediente and obj.expediente.cliente:
            avisos.notificar_cliente(
                obj.expediente.cliente, f"Avance en su proceso {obj.expediente.numero}",
                f"El despacho preparó y aprobó una {self.etiqueta} en su proceso {obj.expediente.numero}.",
                f"escrito:{self.etiqueta}:{obj.pk}:aprobado",
            )
        return self._responder(obj)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def devolver(self, request, pk=None):
        """El abogado devuelve el escrito pendiente con el motivo, para que lo ajusten."""
        obj = self.get_object()
        if obj.aprobacion != "pendiente":
            raise ValidationError({"detail": "Solo se puede devolver un escrito pendiente de aprobación."})
        motivo = (request.data.get("motivo") or "").strip()
        if len(motivo) < 3:
            raise ValidationError({"motivo": "Indique qué debe ajustarse."})
        obj.aprobacion, obj.aprobado_por, obj.aprobado_en, obj.motivo_devolucion = "devuelto", None, None, motivo
        obj.save(update_fields=["aprobacion", "aprobado_por", "aprobado_en", "motivo_devolucion"])
        avisos.notificar_borrador_resuelto(obj, self.etiqueta, request.user, aprobado=False)
        return self._responder(obj)


class DemandaViewSet(AlcanceAbogadoMixin, viewsets.ModelViewSet):
    serializer_class = DemandaSerializer
    etiqueta = "demanda"
    estados_con_aprobacion = ("radicada", "inadmitida", "admitida", "rechazada")
    relaciones = ("cliente", "expediente", "juzgado", "abogado_responsable")

    def queryset_base(self):
        return Demanda.objects.all()

    @action(detail=True, methods=["get"], url_path="generar-borrador")
    def generar_borrador(self, request, pk=None):
        """Texto base del escrito de demanda con los datos registrados (no lo guarda)."""
        return Response({"borrador": borrador_demanda(self.get_object())})


class ContestacionViewSet(AlcanceAbogadoMixin, viewsets.ModelViewSet):
    serializer_class = ContestacionSerializer
    etiqueta = "contestación"
    estados_con_aprobacion = ("presentada",)
    relaciones = ("cliente", "expediente", "juzgado", "abogado_responsable")

    def queryset_base(self):
        return ContestacionDemanda.objects.all()

    @action(detail=True, methods=["get"], url_path="generar-borrador")
    def generar_borrador(self, request, pk=None):
        return Response({"borrador": borrador_contestacion(self.get_object())})


class CitacionViewSet(AlcanceAbogadoMixin, viewsets.ModelViewSet):
    serializer_class = CitacionSerializer
    etiqueta = "citación"
    estados_con_aprobacion = ("enviada", "entregada", "devuelta", "notificado")
    relaciones = ("demanda", "expediente", "abogado_responsable")

    def queryset_base(self):
        return Citacion.objects.all()
