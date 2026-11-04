from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permisos import expedientes_visibles
from expedientes import eventos

from .models import AcuerdoPago
from .serializers import AcuerdoPagoSerializer


def pesos(valor):
    return "$" + f"{Decimal(valor):,.0f}".replace(",", ".")


class AcuerdoPagoViewSet(viewsets.ModelViewSet):
    serializer_class = AcuerdoPagoSerializer

    def get_queryset(self):
        qs = (
            AcuerdoPago.objects.filter(expediente__in=expedientes_visibles(self.request.user))
            .select_related("expediente")
            .prefetch_related("cuotas")
        )
        expediente = self.request.query_params.get("expediente")
        if expediente and expediente.isdigit():
            qs = qs.filter(expediente_id=expediente)
        return qs

    def _respuesta(self, acuerdo):
        acuerdo = self.get_queryset().get(pk=acuerdo.pk)
        return Response(self.get_serializer(acuerdo).data)

    # Cada movimiento queda en el historial de cambios del expediente
    @transaction.atomic
    def perform_create(self, serializer):
        acuerdo = serializer.save(creado_por=self.request.user)
        eventos.registrar(
            acuerdo.expediente, self.request.user, "Acuerdo de pago registrado",
            [("Acuerdo de pago", "—", f"{acuerdo.concepto} · {pesos(acuerdo.valor_total)}")],
        )

    def perform_update(self, serializer):
        anterior = serializer.instance.estado
        acuerdo = serializer.save()
        if anterior != acuerdo.estado:
            nombres = dict(AcuerdoPago.Estado.choices)
            eventos.registrar(
                acuerdo.expediente, self.request.user, "Acuerdo de pago modificado",
                [(f"Acuerdo «{acuerdo.concepto}» · Estado", nombres[anterior], nombres[acuerdo.estado])],
            )

    def perform_destroy(self, instance):
        eventos.registrar(
            instance.expediente, self.request.user, "Acuerdo de pago eliminado",
            [("Acuerdo de pago", f"{instance.concepto} · {pesos(instance.valor_total)}", "—")],
        )
        instance.delete()

    def _cuota(self, acuerdo, request):
        cuota_id = request.data.get("cuota")
        cuota = acuerdo.cuotas.filter(pk=cuota_id).first() if str(cuota_id).isdigit() else None
        if cuota is None:
            raise serializers.ValidationError({"cuota": "Indique una cuota de este acuerdo."})
        if acuerdo.estado == AcuerdoPago.Estado.CANCELADO:
            raise serializers.ValidationError({"detail": "El acuerdo está cancelado."})
        return cuota

    @action(detail=True, methods=["post"])
    def pagar(self, request, pk=None):
        """Registra el pago de una cuota. Cuerpo: {cuota, fecha_pago (opcional, por defecto hoy)}."""
        acuerdo = self.get_object()
        cuota = self._cuota(acuerdo, request)
        if cuota.fecha_pago:
            raise serializers.ValidationError({"detail": "La cuota ya está pagada."})
        fecha = request.data.get("fecha_pago") or timezone.localdate().isoformat()
        campo = serializers.DateField()
        try:
            fecha = campo.to_internal_value(fecha)
        except serializers.ValidationError:
            raise serializers.ValidationError({"fecha_pago": "Fecha inválida."})
        if fecha > timezone.localdate():
            raise serializers.ValidationError({"fecha_pago": "La fecha de pago no puede ser futura."})
        cuota.fecha_pago = fecha
        cuota.save(update_fields=["fecha_pago"])
        eventos.registrar(
            acuerdo.expediente, request.user, "Cuota de acuerdo pagada",
            [(f"Acuerdo «{acuerdo.concepto}» · Cuota {cuota.numero} ({pesos(cuota.valor)})", "Pendiente", "Pagada")],
        )
        return self._respuesta(acuerdo)

    @action(detail=True, methods=["post"])
    def reabrir(self, request, pk=None):
        """Deshace el pago de una cuota (por si se registró por error)."""
        acuerdo = self.get_object()
        cuota = self._cuota(acuerdo, request)
        if not cuota.fecha_pago:
            raise serializers.ValidationError({"detail": "La cuota no está pagada."})
        cuota.fecha_pago = None
        cuota.save(update_fields=["fecha_pago"])
        eventos.registrar(
            acuerdo.expediente, request.user, "Pago de cuota revertido",
            [(f"Acuerdo «{acuerdo.concepto}» · Cuota {cuota.numero} ({pesos(cuota.valor)})", "Pagada", "Pendiente")],
        )
        return self._respuesta(acuerdo)
