from django.utils import timezone
from rest_framework import serializers

from core.permisos import es_directivo, exigir_expediente_visible

from .models import Factura


class FacturaSerializer(serializers.ModelSerializer):
    expediente_numero = serializers.CharField(source="expediente.numero", read_only=True, default=None)
    cliente_nombre = serializers.CharField(source="cliente.nombre", read_only=True, default=None)

    class Meta:
        model = Factura
        fields = "__all__"
        read_only_fields = ["fecha_pago"]
        extra_kwargs = {
            "expediente": {"required": False, "allow_null": True},
            "cliente": {"required": False, "allow_null": True},
        }

    def validate_numero(self, value):
        value = value.strip().upper()
        if len(value) < 3:
            raise serializers.ValidationError("El número de factura es demasiado corto.")
        # Se normaliza a mayúsculas, así que la unicidad se comprueba sobre el valor normalizado
        repetidas = Factura.objects.filter(numero=value)
        if self.instance is not None:
            repetidas = repetidas.exclude(pk=self.instance.pk)
        if repetidas.exists():
            raise serializers.ValidationError(f"Ya existe una factura con el número {value}.")
        return value

    def validate_concepto(self, value):
        value = " ".join(value.split())
        if len(value) < 3:
            raise serializers.ValidationError("Describa el concepto del cobro.")
        return value

    def validate_monto(self, value):
        if value <= 0:
            raise serializers.ValidationError("El monto debe ser mayor que cero.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        inst = self.instance
        expediente = attrs.get("expediente", inst.expediente if inst else None)
        cliente = attrs.get("cliente", inst.cliente if inst else None)

        if "expediente" in attrs:
            exigir_expediente_visible(request, attrs["expediente"])

        # Quien no es socio/administrador solo ve las facturas de sus expedientes:
        # una factura sin expediente quedaría invisible para quien la crea.
        if request and not es_directivo(request.user) and expediente is None:
            raise serializers.ValidationError(
                {"expediente": "Debe asociar la factura a uno de sus expedientes."}
            )

        # El cliente facturado debe ser el del expediente (y se completa solo si falta).
        if expediente is not None and expediente.cliente_id and ("cliente" in attrs or "expediente" in attrs):
            if cliente is None:
                attrs["cliente"] = expediente.cliente
            elif cliente.pk != expediente.cliente_id:
                raise serializers.ValidationError(
                    {"cliente": "El cliente no coincide con el cliente del expediente seleccionado."}
                )

        if "fecha_vencimiento" in attrs and attrs["fecha_vencimiento"]:
            emision = inst.fecha_emision if inst else timezone.localdate()
            if attrs["fecha_vencimiento"] < emision:
                raise serializers.ValidationError(
                    {"fecha_vencimiento": "La fecha de vencimiento no puede ser anterior a la fecha de emisión."}
                )
        return attrs

    # fecha_pago se maneja sola: se fija al pasar la factura a "pagada" y se borra si vuelve a otro estado.
    def create(self, validated_data):
        if validated_data.get("estado") == Factura.Estado.PAGADA:
            validated_data["fecha_pago"] = timezone.localdate()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        nuevo = validated_data.get("estado", instance.estado)
        if nuevo == Factura.Estado.PAGADA:
            if instance.estado != Factura.Estado.PAGADA or instance.fecha_pago is None:
                validated_data["fecha_pago"] = timezone.localdate()
        else:
            validated_data["fecha_pago"] = None
        return super().update(instance, validated_data)
