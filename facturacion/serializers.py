from rest_framework import serializers
from .models import Factura


class FacturaSerializer(serializers.ModelSerializer):
    expediente_numero = serializers.CharField(source="expediente.numero", read_only=True)

    class Meta:
        model = Factura
        fields = "__all__"