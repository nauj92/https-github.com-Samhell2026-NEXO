from rest_framework import serializers

from audiencias.models import Audiencia
from expedientes.models import EtapaProceso, Expediente
from facturacion.models import Factura

from .models import Mensaje


class MensajeSerializer(serializers.ModelSerializer):
    autor_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Mensaje
        fields = ["id", "expediente", "autor_nombre", "de_cliente", "texto", "creado_en"]
        read_only_fields = ["id", "expediente", "autor_nombre", "de_cliente", "creado_en"]

    def get_autor_nombre(self, obj):
        if obj.autor is None:
            return ""
        return obj.autor.get_full_name() or obj.autor.username

    def validate_texto(self, valor):
        valor = valor.strip()
        if not valor:
            raise serializers.ValidationError("Escriba el mensaje.")
        return valor


class EtapaPortalSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtapaProceso
        fields = ["id", "nombre", "fecha_limite", "estado"]


class AudienciaPortalSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = Audiencia
        fields = ["id", "tipo", "tipo_display", "clase", "fecha_hora", "lugar"]


class ExpedientePortalSerializer(serializers.ModelSerializer):
    """Lo que el cliente ve de su proceso: datos generales, etapas y audiencias (sin notas internas)."""

    juzgado_nombre = serializers.CharField(source="juzgado.nombre", read_only=True)
    abogado_nombre = serializers.SerializerMethodField()
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    etapas = EtapaPortalSerializer(many=True, read_only=True)
    audiencias = AudienciaPortalSerializer(many=True, read_only=True)

    class Meta:
        model = Expediente
        fields = [
            "id", "numero", "juzgado_nombre", "materia", "demandante", "demandado", "estado", "estado_display",
            "abogado_nombre", "etapas", "audiencias",
        ]

    def get_abogado_nombre(self, obj):
        a = obj.abogado_asignado
        return a.get_full_name() or a.username


class FacturaPortalSerializer(serializers.ModelSerializer):
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)

    class Meta:
        model = Factura
        fields = ["id", "numero", "concepto", "monto", "estado", "estado_display", "fecha_emision", "fecha_vencimiento", "fecha_pago"]
