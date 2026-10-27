from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers

from core.permisos import es_directivo, exigir_expediente_visible
from core.plazos import sumar_dias_habiles

from .models import DocumentoExpediente, EtapaProceso, Expediente, Juzgado
from .validators import normalizar_radicado, validar_radicado


class JuzgadoSerializer(serializers.ModelSerializer):
    etiqueta = serializers.CharField(read_only=True)

    class Meta:
        model = Juzgado
        fields = "__all__"
        extra_kwargs = {"codigo": {"required": False, "allow_null": True}}

    def validate_codigo(self, value):
        if value in (None, ""):
            return None
        value = value.strip()
        if not (value.isdigit() and len(value) == 12):
            raise serializers.ValidationError("El código del despacho debe tener 12 dígitos.")
        return value

    def validate(self, attrs):
        # Si solo llegan los datos de la Rama Judicial, se completan los campos antiguos (ciudad y materia).
        if not attrs.get("ciudad") and attrs.get("municipio"):
            attrs["ciudad"] = attrs["municipio"]
        if not attrs.get("materia") and attrs.get("especialidad"):
            attrs["materia"] = attrs["especialidad"].lower()
        return attrs

    def validate_nombre(self, value):
        value = " ".join(value.split())
        if len(value) < 5:
            raise serializers.ValidationError("El nombre del juzgado es demasiado corto.")
        return value


class EtapaProcesoSerializer(serializers.ModelSerializer):
    # Opcional: si se envía y no hay fecha_limite, se calcula en días hábiles desde hoy.
    dias_habiles = serializers.IntegerField(write_only=True, required=False, min_value=1, max_value=365)
    dias_restantes = serializers.SerializerMethodField()

    class Meta:
        model = EtapaProceso
        fields = "__all__"

    def get_dias_restantes(self, obj):
        """Días calendario hasta la fecha límite (negativo = vencida). None si no aplica."""
        if not obj.fecha_limite or obj.estado == EtapaProceso.Estado.COMPLETADA:
            return None
        return (obj.fecha_limite - timezone.localdate()).days

    def validate_expediente(self, value):
        exigir_expediente_visible(self.context.get("request"), value)
        return value

    def validate(self, attrs):
        dias = attrs.pop("dias_habiles", None)
        if dias and not attrs.get("fecha_limite"):
            attrs["fecha_limite"] = sumar_dias_habiles(timezone.localdate(), dias)
        return attrs


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

    def validate_numero(self, value):
        # Expedientes antiguos (p. ej. con 20 dígitos) siguen siendo editables mientras no se cambie su número;
        # el formato de 23 dígitos se exige al crear o al modificar el radicado.
        if self.instance is not None and normalizar_radicado(value) == normalizar_radicado(self.instance.numero):
            return self.instance.numero
        try:
            numero = validar_radicado(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages[0])
        # El radicado se guarda normalizado, así que la unicidad se comprueba sobre ese valor
        repetidos = Expediente.objects.filter(numero=numero)
        if self.instance is not None:
            repetidos = repetidos.exclude(pk=self.instance.pk)
        if repetidos.exists():
            raise serializers.ValidationError("Ya existe un expediente con ese radicado.")
        return numero

    def validate_demandante(self, value):
        return self._limpiar_parte(value, "demandante")

    def validate_demandado(self, value):
        return self._limpiar_parte(value, "demandado")

    @staticmethod
    def _limpiar_parte(value, campo):
        value = " ".join(value.split())
        if len(value) < 3:
            raise serializers.ValidationError(f"Indique el nombre completo del {campo}.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        abogado = attrs.get("abogado_asignado")
        # Un abogado o secretario no puede pasar sus expedientes a otra persona.
        if request and abogado and not es_directivo(request.user) and abogado != request.user:
            raise serializers.ValidationError(
                {"abogado_asignado": "Solo un socio o un administrador puede asignar expedientes a otro abogado."}
            )
        return attrs


class DocumentoExpedienteSerializer(serializers.ModelSerializer):
    """Metadatos del documento (el contenido se descarga por un endpoint aparte)."""

    subido_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = DocumentoExpediente
        fields = ["id", "expediente", "nombre", "tipo_contenido", "tamano", "subido_por", "subido_por_nombre", "subido_en"]
        read_only_fields = fields

    def get_subido_por_nombre(self, obj):
        if not obj.subido_por:
            return None
        return obj.subido_por.get_full_name() or obj.subido_por.username
