from rest_framework import serializers
from .models import Audiencia


class AudienciaSerializer(serializers.ModelSerializer):
    expediente_numero = serializers.CharField(source="expediente.numero", read_only=True)

    class Meta:
        model = Audiencia
        fields = "__all__"