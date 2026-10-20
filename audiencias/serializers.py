from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from core.permisos import exigir_expediente_visible
from expedientes.models import Expediente

from .models import Audiencia

# Separación mínima entre dos audiencias del mismo abogado (supuesto de la aplicación)
SEPARACION_MINIMA = timedelta(hours=1)


class AudienciaSerializer(serializers.ModelSerializer):
    expediente_numero = serializers.CharField(source="expediente.numero", read_only=True)
    expediente_juzgado = serializers.CharField(source="expediente.juzgado.nombre", read_only=True)
    expediente_abogado = serializers.SerializerMethodField()

    class Meta:
        model = Audiencia
        fields = "__all__"

    def get_expediente_abogado(self, obj):
        abogado = obj.expediente.abogado_asignado
        nombre = abogado.get_full_name()
        return nombre if nombre else abogado.username

    def validate_lugar(self, value):
        value = " ".join(value.split())
        if len(value) < 3:
            raise serializers.ValidationError("Indique el lugar o la sala donde se realizará la audiencia.")
        return value

    def validate_fecha_hora(self, value):
        # Al programar una audiencia nueva la fecha debe ser futura (al editar se permite corregir registros).
        if self.instance is None and value < timezone.now():
            raise serializers.ValidationError("La fecha y hora de la audiencia no pueden estar en el pasado.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        inst = self.instance
        expediente = attrs.get("expediente", inst.expediente if inst else None)
        fecha = attrs.get("fecha_hora", inst.fecha_hora if inst else None)

        if "expediente" in attrs:
            exigir_expediente_visible(request, attrs["expediente"])
            cambia = inst is None or inst.expediente_id != attrs["expediente"].pk
            if cambia and attrs["expediente"].estado == Expediente.Estado.CERRADO:
                raise serializers.ValidationError(
                    {"expediente": "No se pueden programar audiencias en un expediente cerrado."}
                )

        # El mismo abogado no puede tener dos audiencias a la vez.
        if expediente is not None and fecha is not None and ("fecha_hora" in attrs or "expediente" in attrs):
            choque = (
                Audiencia.objects.filter(
                    expediente__abogado_asignado=expediente.abogado_asignado,
                    fecha_hora__gt=fecha - SEPARACION_MINIMA,
                    fecha_hora__lt=fecha + SEPARACION_MINIMA,
                )
                .exclude(pk=inst.pk if inst else None)
                .select_related("expediente")
                .first()
            )
            if choque:
                otra = timezone.localtime(choque.fecha_hora)
                raise serializers.ValidationError(
                    {
                        "fecha_hora": (
                            f"El abogado ya tiene otra audiencia a esa hora (expediente {choque.expediente.numero}, "
                            f"{otra:%d/%m/%Y %H:%M}). Deben separarse al menos una hora."
                        )
                    }
                )
        return attrs
