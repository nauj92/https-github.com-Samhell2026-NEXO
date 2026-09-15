from rest_framework import serializers
from .models import Juzgado, Expediente, EtapaProceso


class JuzgadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Juzgado
        fields = "__all__"


class EtapaProcesoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtapaProceso
        fields = "__all__"


class ExpedienteSerializer(serializers.ModelSerializer):
    etapas = EtapaProcesoSerializer(many=True, read_only=True)
    abogado_asignado_nombre = serializers.SerializerMethodField()
    juzgado_nombre = serializers.CharField(source="juzgado.nombre", read_only=True)
    cliente_nombre = serializers.CharField(source="cliente.nombre", read_only=True, default=None)

    class Meta:
        model = Expediente
        fields = "__all__"
        extra_kwargs = {
            "abogado_asignado": {"required": False},
            "cliente": {"required": False, "allow_null": True},
        }

    def get_abogado_asignado_nombre(self, obj):
        nombre_completo = obj.abogado_asignado.get_full_name()
        return nombre_completo if nombre_completo else obj.abogado_asignado.username