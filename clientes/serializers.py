import re

from rest_framework import serializers

from .models import Cliente

# El formulario envía "PA" para pasaporte; también se acepta la palabra completa.
TIPOS_DOCUMENTO = {"CC": "CC", "CE": "CE", "NIT": "NIT", "PA": "PA", "PASAPORTE": "PA"}


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = "__all__"

    def validate_nombre(self, value):
        value = " ".join(value.split())
        if len(value) < 3:
            raise serializers.ValidationError("Indique el nombre completo del cliente.")
        return value

    def validate_tipo_documento(self, value):
        canonico = TIPOS_DOCUMENTO.get(value.strip().upper())
        if canonico is None:
            raise serializers.ValidationError("Tipo de documento no válido. Use CC, CE, NIT o PA (pasaporte).")
        return canonico

    def validate_telefono(self, value):
        if not value:
            return value
        digitos = re.sub(r"\D", "", value)
        if not re.fullmatch(r"[\d\s()+\-]+", value) or not 7 <= len(digitos) <= 15:
            raise serializers.ValidationError("Teléfono no válido: use entre 7 y 15 dígitos (ej. 3001234567).")
        return value.strip()

    def validate(self, attrs):
        inst = self.instance
        tipo = attrs.get("tipo_documento", inst.tipo_documento if inst else "CC")
        if "numero_documento" in attrs or "tipo_documento" in attrs:
            bruto = attrs.get("numero_documento", inst.numero_documento if inst else "")
            attrs["numero_documento"] = self._normalizar_documento(tipo, bruto)
            repetido = Cliente.objects.filter(numero_documento=attrs["numero_documento"])
            if inst:
                repetido = repetido.exclude(pk=inst.pk)
            if repetido.exists():
                raise serializers.ValidationError(
                    {"numero_documento": f"Ya existe un cliente registrado con el documento {attrs['numero_documento']}."}
                )
        return attrs

    @staticmethod
    def _normalizar_documento(tipo, valor):
        limpio = re.sub(r"[\s.]", "", valor or "")
        if tipo in ("CC", "CE"):
            if not limpio.isdigit() or not 6 <= len(limpio) <= 10:
                raise serializers.ValidationError(
                    {"numero_documento": f"El número de {tipo} debe tener entre 6 y 10 dígitos, sin letras."}
                )
        elif tipo == "NIT":
            # 9 dígitos, con o sin dígito de verificación (900123456 o 900123456-7)
            if not re.fullmatch(r"\d{9}(-?\d)?", limpio):
                raise serializers.ValidationError(
                    {"numero_documento": "El NIT debe tener 9 dígitos y, opcionalmente, el dígito de verificación (ej. 900123456-7)."}
                )
            if len(limpio) == 10 and "-" not in limpio:
                limpio = f"{limpio[:9]}-{limpio[9]}"
        else:  # PA = pasaporte
            if not re.fullmatch(r"[A-Za-z0-9]{5,15}", limpio):
                raise serializers.ValidationError(
                    {"numero_documento": "El pasaporte debe tener entre 5 y 15 letras o números."}
                )
            limpio = limpio.upper()
        return limpio
