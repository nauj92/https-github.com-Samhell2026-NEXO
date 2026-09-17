from rest_framework import serializers
from .models import Factura


class FacturaSerializer(serializers.ModelSerializer):
    expediente_numero = serializers.CharField(source="expediente.numero", read_only=True, default=None)
    cliente_nombre = serializers.CharField(source="cliente.nombre", read_only=True, default=None)

    class Meta:
        model = Factura
        fields = "__all__"
        extra_kwargs = {
            "expediente": {"required": False, "allow_null": True},
            "cliente": {"required": False, "allow_null": True},
        }