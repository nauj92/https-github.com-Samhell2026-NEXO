from rest_framework import serializers
from .models import Audiencia


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