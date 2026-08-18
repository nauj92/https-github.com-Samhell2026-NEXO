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
    abogado_asignado_nombre = serializers.CharField(source="abogado_asignado.get_full_name", read_only=True)
    juzgado_nombre = serializers.CharField(source="juzgado.nombre", read_only=True)

    class Meta:
        model = Expediente
        fields = "__all__"