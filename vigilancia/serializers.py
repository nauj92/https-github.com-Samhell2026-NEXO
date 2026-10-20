from django.utils import timezone
from rest_framework import serializers

from core.permisos import exigir_expediente_visible
from expedientes.models import Expediente

from .models import ActuacionVigilancia, EnlaceVigilancia, Vigilancia


class ActuacionSerializer(serializers.ModelSerializer):
    registrada_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = ActuacionVigilancia
        fields = ["id", "fecha", "descripcion", "registrada_por_nombre", "registrada_en"]
        read_only_fields = ["id", "registrada_por_nombre", "registrada_en"]

    def get_registrada_por_nombre(self, obj):
        if not obj.registrada_por:
            return None
        return obj.registrada_por.get_full_name() or obj.registrada_por.username

    def validate_fecha(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError("La fecha de la actuación no puede ser futura.")
        return value

    def validate_descripcion(self, value):
        value = " ".join(value.split())
        if len(value) < 5:
            raise serializers.ValidationError("Describa la actuación (mínimo 5 caracteres).")
        return value


class EnlaceSerializer(serializers.ModelSerializer):
    creado_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = EnlaceVigilancia
        fields = ["id", "titulo", "url", "nota", "creado_por_nombre", "creado_en"]
        read_only_fields = ["id", "creado_por_nombre", "creado_en"]

    def get_creado_por_nombre(self, obj):
        if not obj.creado_por:
            return None
        return obj.creado_por.get_full_name() or obj.creado_por.username

    def validate_titulo(self, value):
        value = " ".join(value.split())
        if len(value) < 3:
            raise serializers.ValidationError("Escriba un título para el enlace (mínimo 3 caracteres).")
        return value

    def validate_url(self, value):
        # Solo http/https: evita esquemas peligrosos (javascript:, data:, file:) que se ejecutarían al hacer clic
        if not value.lower().startswith(("http://", "https://")):
            raise serializers.ValidationError("El enlace debe comenzar con http:// o https://")
        return value


class VigilanciaSerializer(serializers.ModelSerializer):
    # Explícito para que la unicidad la valide validate_expediente con un mensaje en español
    expediente = serializers.PrimaryKeyRelatedField(queryset=Expediente.objects.all())
    expediente_numero = serializers.CharField(source="expediente.numero", read_only=True)
    juzgado_nombre = serializers.CharField(source="expediente.juzgado.nombre", read_only=True)
    demandante = serializers.CharField(source="expediente.demandante", read_only=True)
    demandado = serializers.CharField(source="expediente.demandado", read_only=True)
    ultima_actuacion = serializers.SerializerMethodField()
    ultima_descripcion = serializers.SerializerMethodField()
    dias_sin_movimiento = serializers.SerializerMethodField()
    alerta = serializers.SerializerMethodField()
    total_actuaciones = serializers.SerializerMethodField()
    total_enlaces = serializers.SerializerMethodField()

    class Meta:
        model = Vigilancia
        fields = [
            "id", "expediente", "expediente_numero", "juzgado_nombre", "demandante", "demandado",
            "activa", "dias_alerta", "observaciones", "ultima_actuacion", "ultima_descripcion",
            "dias_sin_movimiento", "alerta", "total_actuaciones", "total_enlaces", "creado_en",
        ]
        read_only_fields = ["id", "creado_en"]

    def get_ultima_actuacion(self, obj):
        ultima = obj.ultima_actuacion()
        return ultima.fecha if ultima else None

    def get_ultima_descripcion(self, obj):
        ultima = obj.ultima_actuacion()
        return ultima.descripcion if ultima else None

    def get_dias_sin_movimiento(self, obj):
        return obj.dias_sin_movimiento()

    def get_alerta(self, obj):
        return obj.en_alerta()

    def get_total_actuaciones(self, obj):
        return len(obj.actuaciones.all())

    def get_total_enlaces(self, obj):
        return len(obj.enlaces.all())

    def validate_dias_alerta(self, value):
        if not 1 <= value <= 365:
            raise serializers.ValidationError("Los días de alerta deben estar entre 1 y 365.")
        return value

    def validate_expediente(self, value):
        if self.instance is not None and value != self.instance.expediente:
            raise serializers.ValidationError("No se puede cambiar el expediente de una vigilancia.")
        exigir_expediente_visible(self.context.get("request"), value)
        if self.instance is None:
            if value.estado == Expediente.Estado.CERRADO:
                raise serializers.ValidationError("El expediente está cerrado.")
            if Vigilancia.objects.filter(expediente=value).exists():
                raise serializers.ValidationError("Ese expediente ya está en vigilancia.")
        return value
