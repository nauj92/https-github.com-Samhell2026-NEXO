import json

from django.core.serializers.json import DjangoJSONEncoder
from rest_framework import serializers

from core import liquidaciones as motor
from core.permisos import exigir_expediente_visible

from .models import Liquidacion

DINERO = {"max_digits": 16, "decimal_places": 2}


class PeriodoTasaSerializer(serializers.Serializer):
    desde = serializers.DateField()
    hasta = serializers.DateField()
    tasa_ea = serializers.DecimalField(max_digits=7, decimal_places=3, min_value=0, max_value=200)


class AbonoSerializer(serializers.Serializer):
    fecha = serializers.DateField()
    valor = serializers.DecimalField(min_value=1, **DINERO)


class ExtraordinariaSerializer(serializers.Serializer):
    concepto = serializers.CharField(max_length=100, required=False, allow_blank=True)
    fecha_vencimiento = serializers.DateField()
    valor = serializers.DecimalField(min_value=1, **DINERO)


class LaboralEntradaSerializer(serializers.Serializer):
    salario_mensual = serializers.DecimalField(min_value=1, **DINERO)
    auxilio_transporte = serializers.DecimalField(min_value=0, default=0, **DINERO)
    fecha_inicio = serializers.DateField()
    fecha_fin = serializers.DateField()
    desde_cesantias = serializers.DateField(required=False, allow_null=True)
    desde_prima = serializers.DateField(required=False, allow_null=True)
    desde_vacaciones = serializers.DateField(required=False, allow_null=True)
    dias_vacaciones_disfrutados = serializers.IntegerField(min_value=0, max_value=5000, default=0)
    salarios_pendientes_dias = serializers.IntegerField(min_value=0, max_value=60, default=0)
    deducciones = serializers.DecimalField(min_value=0, default=0, **DINERO)
    indemnizacion = serializers.BooleanField(default=False)
    tipo_contrato = serializers.ChoiceField(choices=["indefinido", "fijo"], default="indefinido")
    fecha_fin_pactada = serializers.DateField(required=False, allow_null=True)
    salario_minimo = serializers.DecimalField(required=False, allow_null=True, min_value=1, **DINERO)

    def calcular(self, d):
        return motor.liquidar_laboral(**d)


class CreditoEntradaSerializer(serializers.Serializer):
    capital = serializers.DecimalField(min_value=1, **DINERO)
    fecha_inicio_mora = serializers.DateField()
    fecha_corte = serializers.DateField()
    tasa_ea = serializers.DecimalField(max_digits=7, decimal_places=3, min_value=0, max_value=200, required=False, allow_null=True)
    periodos = PeriodoTasaSerializer(many=True, required=False)
    abonos = AbonoSerializer(many=True, required=False)
    costas = serializers.DecimalField(min_value=0, default=0, **DINERO)
    otros = serializers.DecimalField(min_value=0, default=0, **DINERO)

    def calcular(self, d):
        return motor.liquidar_credito(**d)


class CuotasEntradaSerializer(serializers.Serializer):
    valor_cuota = serializers.DecimalField(min_value=1, **DINERO)
    mes_inicial = serializers.DateField()
    mes_final = serializers.DateField()
    dia_vencimiento = serializers.IntegerField(min_value=1, max_value=28)
    fecha_corte = serializers.DateField()
    tasa_ea = serializers.DecimalField(max_digits=7, decimal_places=3, min_value=0, max_value=200)
    extraordinarias = ExtraordinariaSerializer(many=True, required=False)
    abonos_total = serializers.DecimalField(min_value=0, default=0, **DINERO)

    def calcular(self, d):
        return motor.liquidar_cuotas_administracion(**d)


class AlimentosEntradaSerializer(serializers.Serializer):
    valor_cuota = serializers.DecimalField(min_value=1, **DINERO)
    mes_inicial = serializers.DateField()
    mes_final = serializers.DateField()
    dia_vencimiento = serializers.IntegerField(min_value=1, max_value=28)
    fecha_corte = serializers.DateField()
    tasa_ea = serializers.DecimalField(max_digits=7, decimal_places=3, min_value=0, max_value=200, default=0)
    incremento_anual = serializers.DecimalField(max_digits=6, decimal_places=3, min_value=0, max_value=100, default=0)
    adicionales = ExtraordinariaSerializer(many=True, required=False)
    abonos_total = serializers.DecimalField(min_value=0, default=0, **DINERO)

    def calcular(self, d):
        return motor.liquidar_alimentos(**d)


ENTRADAS = {
    "laboral": LaboralEntradaSerializer,
    "credito": CreditoEntradaSerializer,
    "cuotas": CuotasEntradaSerializer,
    "alimentos": AlimentosEntradaSerializer,
}


def calcular_liquidacion(tipo, datos):
    """Valida los datos de entrada del tipo dado y calcula. Devuelve (datos_normalizados, resultado)."""
    if tipo not in ENTRADAS:
        raise serializers.ValidationError({"tipo": "Tipo de liquidación no válido (laboral, credito, cuotas o alimentos)."})
    entrada = ENTRADAS[tipo](data=datos or {})
    if not entrada.is_valid():
        raise serializers.ValidationError({"datos": entrada.errors})
    try:
        resultado = entrada.calcular(entrada.validated_data)
    except motor.ErrorLiquidacion as exc:
        raise serializers.ValidationError({"datos": [str(exc)]})
    normalizados = json.loads(json.dumps(entrada.validated_data, cls=DjangoJSONEncoder))
    return normalizados, resultado


class CalcularSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=list(ENTRADAS))
    datos = serializers.DictField()


class LiquidacionSerializer(serializers.ModelSerializer):
    datos = serializers.DictField()
    creado_por_nombre = serializers.SerializerMethodField()
    expediente_numero = serializers.CharField(source="expediente.numero", read_only=True, default=None)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = Liquidacion
        fields = [
            "id", "tipo", "tipo_display", "referencia", "expediente", "expediente_numero", "datos",
            "resultado", "total", "creado_por_nombre", "creado_en",
        ]
        read_only_fields = ["id", "resultado", "total", "creado_en", "tipo_display"]

    def get_creado_por_nombre(self, obj):
        if not obj.creado_por:
            return None
        return obj.creado_por.get_full_name() or obj.creado_por.username

    def validate_referencia(self, value):
        return " ".join(value.split())

    def validate_expediente(self, value):
        exigir_expediente_visible(self.context.get("request"), value)
        return value

    def validate(self, attrs):
        if self.instance is not None:
            # No se edita una liquidación guardada: se crea otra con los datos nuevos
            raise serializers.ValidationError("Una liquidación guardada no se modifica; cree una nueva.")
        if not attrs.get("referencia"):
            raise serializers.ValidationError({"referencia": "Escriba un nombre o asunto para guardarla."})
        datos, resultado = calcular_liquidacion(attrs["tipo"], attrs["datos"])
        attrs["datos"] = datos
        attrs["resultado"] = resultado
        attrs["total"] = resultado["total"]
        return attrs
