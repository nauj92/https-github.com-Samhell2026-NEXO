import calendar
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.utils import timezone
from rest_framework import serializers

from core.permisos import exigir_expediente_visible
from expedientes.models import Expediente

from .models import AcuerdoPago, CuotaAcuerdo

MAX_CUOTAS = 120


def sumar_meses(fecha, meses):
    """Misma fecha unos meses después; si el mes no tiene ese día (31), usa el último."""
    indice = fecha.month - 1 + meses
    anio, mes = fecha.year + indice // 12, indice % 12 + 1
    return date(anio, mes, min(fecha.day, calendar.monthrange(anio, mes)[1]))


def repartir(total, n):
    """n valores que suman exactamente `total`; la última cuota absorbe el redondeo."""
    base = (total / n).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    valores = [base] * (n - 1)
    valores.append(total - base * (n - 1))
    return valores


class CuotaSerializer(serializers.ModelSerializer):
    pagada = serializers.SerializerMethodField()
    en_mora = serializers.SerializerMethodField()

    class Meta:
        model = CuotaAcuerdo
        fields = ["id", "numero", "valor", "fecha_vencimiento", "fecha_pago", "pagada", "en_mora"]

    def get_pagada(self, obj):
        return obj.fecha_pago is not None

    def get_en_mora(self, obj):
        return obj.fecha_pago is None and obj.fecha_vencimiento < timezone.localdate()


class AcuerdoPagoSerializer(serializers.ModelSerializer):
    expediente_numero = serializers.CharField(source="expediente.numero", read_only=True)
    cuotas = CuotaSerializer(many=True, read_only=True)
    total_pagado = serializers.SerializerMethodField()
    saldo = serializers.SerializerMethodField()
    estado_actual = serializers.SerializerMethodField()
    # Solo al crear: así se generan las cuotas mensuales
    num_cuotas = serializers.IntegerField(write_only=True, required=False, min_value=1, max_value=MAX_CUOTAS)
    fecha_primera_cuota = serializers.DateField(write_only=True, required=False)

    class Meta:
        model = AcuerdoPago
        fields = [
            "id", "expediente", "expediente_numero", "deudor", "concepto", "valor_total", "fecha_acuerdo",
            "estado", "observaciones", "cuotas", "total_pagado", "saldo", "estado_actual",
            "num_cuotas", "fecha_primera_cuota",
        ]

    def get_total_pagado(self, obj):
        return obj.total_pagado()

    def get_saldo(self, obj):
        return obj.saldo()

    def get_estado_actual(self, obj):
        return obj.estado_actual()

    def validate_deudor(self, value):
        value = " ".join(value.split())
        if len(value) < 3:
            raise serializers.ValidationError("Indique quién se obliga a pagar.")
        return value

    def validate_concepto(self, value):
        value = " ".join(value.split())
        if len(value) < 3:
            raise serializers.ValidationError("Indique el concepto del acuerdo.")
        return value

    def validate_valor_total(self, value):
        if value <= 0:
            raise serializers.ValidationError("El valor total debe ser mayor que cero.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        inst = self.instance
        if inst is None:
            faltan = [c for c in ("expediente", "num_cuotas", "fecha_primera_cuota") if c not in attrs]
            if faltan:
                raise serializers.ValidationError({c: "Este campo es obligatorio." for c in faltan})
            exigir_expediente_visible(request, attrs["expediente"])
            if attrs["expediente"].estado == Expediente.Estado.CERRADO:
                raise serializers.ValidationError({"expediente": "No se pueden registrar acuerdos en un expediente cerrado."})
            if attrs["fecha_primera_cuota"] < attrs["fecha_acuerdo"]:
                raise serializers.ValidationError({"fecha_primera_cuota": "La primera cuota no puede vencer antes de la fecha del acuerdo."})
            if attrs["valor_total"] < Decimal(attrs["num_cuotas"]) * Decimal("0.01"):
                raise serializers.ValidationError({"num_cuotas": "El valor total es muy bajo para ese número de cuotas."})
        else:
            # Al editar solo se corrigen datos descriptivos; el valor y las cuotas no cambian.
            if "expediente" in attrs and attrs["expediente"].pk != inst.expediente_id:
                raise serializers.ValidationError({"expediente": "No se puede cambiar el expediente del acuerdo."})
            if "valor_total" in attrs and attrs["valor_total"] != inst.valor_total:
                raise serializers.ValidationError({"valor_total": "El valor no se puede modificar. Cancele el acuerdo y registre uno nuevo."})
            for campo in ("num_cuotas", "fecha_primera_cuota"):
                attrs.pop(campo, None)
        return attrs

    def create(self, validated_data):
        n = validated_data.pop("num_cuotas")
        primera = validated_data.pop("fecha_primera_cuota")
        acuerdo = AcuerdoPago.objects.create(**validated_data)
        valores = repartir(acuerdo.valor_total, n)
        CuotaAcuerdo.objects.bulk_create(
            CuotaAcuerdo(acuerdo=acuerdo, numero=i + 1, valor=v, fecha_vencimiento=sumar_meses(primera, i))
            for i, v in enumerate(valores)
        )
        return acuerdo
