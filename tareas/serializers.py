from django.contrib.auth import get_user_model
from rest_framework import serializers

from core.permisos import ROL_CLIENTE, exigir_expediente_visible, puede

from .models import ComprobanteTarea, Tarea

Usuario = get_user_model()

# Quien solo tiene «editar» (sin «crear») únicamente puede cambiar estos campos: marcar el avance de su trámite.
CAMPOS_DE_AVANCE = {"estado", "observacion_cierre"}


class ComprobanteTareaSerializer(serializers.ModelSerializer):
    subido_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = ComprobanteTarea
        fields = ["id", "nombre", "tipo_contenido", "tamano", "subido_por_nombre", "subido_en"]
        read_only_fields = fields

    def get_subido_por_nombre(self, obj):
        if obj.subido_por is None:
            return ""
        return obj.subido_por.get_full_name() or obj.subido_por.username


class TareaSerializer(serializers.ModelSerializer):
    expediente_numero = serializers.CharField(source="expediente.numero", read_only=True, default="")
    asignado_a_nombre = serializers.SerializerMethodField()
    creado_por_nombre = serializers.SerializerMethodField()
    comprobantes = ComprobanteTareaSerializer(many=True, read_only=True)
    vencida = serializers.SerializerMethodField()

    class Meta:
        model = Tarea
        fields = [
            "id", "titulo", "descripcion", "tipo", "expediente", "expediente_numero", "asignado_a",
            "asignado_a_nombre", "creado_por", "creado_por_nombre", "fecha_limite", "estado", "fecha_realizada",
            "observacion_cierre", "comprobantes", "vencida", "creada_en", "actualizada_en",
        ]
        read_only_fields = ["creado_por", "fecha_realizada", "creada_en", "actualizada_en"]

    @staticmethod
    def _nombre(usuario):
        if usuario is None:
            return ""
        return usuario.get_full_name() or usuario.username

    def get_asignado_a_nombre(self, obj):
        return self._nombre(obj.asignado_a)

    def get_creado_por_nombre(self, obj):
        return self._nombre(obj.creado_por)

    def get_vencida(self, obj):
        from django.utils import timezone

        return bool(
            obj.fecha_limite and obj.estado != Tarea.Estado.REALIZADA and obj.fecha_limite < timezone.localdate()
        )

    def validate_asignado_a(self, valor):
        if valor is not None and (not valor.is_active or valor.rol == ROL_CLIENTE):
            raise serializers.ValidationError("Solo se puede asignar a personal activo del despacho.")
        return valor

    def validate_expediente(self, valor):
        request = self.context.get("request")
        if valor is not None and (self.instance is None or valor != self.instance.expediente):
            exigir_expediente_visible(request, valor)
        return valor

    def validate(self, datos):
        request = self.context.get("request")
        if request is not None and self.instance is not None and not puede(request.user, "tareas", "C"):
            sobrantes = set(datos) - CAMPOS_DE_AVANCE
            if sobrantes:
                raise serializers.ValidationError(
                    "Solo puede cambiar el estado de la tarea y la observación de cierre."
                )
        return datos
