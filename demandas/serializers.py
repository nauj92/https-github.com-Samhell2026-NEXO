from django.utils import timezone
from rest_framework import serializers

from core.permisos import es_directivo, exigir_expediente_visible
from core.plazos import sumar_dias_habiles

from .models import Citacion, ContestacionDemanda, Demanda

DIAS_SUBSANACION = 5  # art. 90 CGP: cinco días para subsanar una demanda inadmitida


def limite_subsanacion(demanda):
    """Fecha límite para subsanar (5 días hábiles desde la inadmisión) o None si no aplica."""
    if demanda.estado == Demanda.Estado.INADMITIDA and demanda.fecha_inadmision:
        return sumar_dias_habiles(demanda.fecha_inadmision, DIAS_SUBSANACION)
    return None


class DemandaSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source="cliente.nombre", read_only=True, default=None)
    expediente_numero = serializers.CharField(source="expediente.numero", read_only=True, default=None)
    juzgado_nombre = serializers.CharField(source="juzgado.nombre", read_only=True, default=None)
    abogado_nombre = serializers.SerializerMethodField()
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    fecha_limite_subsanacion = serializers.SerializerMethodField()
    dias_para_subsanar = serializers.SerializerMethodField()

    class Meta:
        model = Demanda
        fields = [
            "id", "clase_proceso", "cliente", "cliente_nombre", "expediente", "expediente_numero",
            "juzgado", "juzgado_nombre", "demandante", "demandado", "pretensiones", "cuantia",
            "estado", "estado_display", "fecha_radicacion", "fecha_inadmision", "fecha_admision",
            "fecha_limite_subsanacion", "dias_para_subsanar", "abogado_responsable", "abogado_nombre",
            "borrador", "observaciones", "creado_en", "actualizado_en",
        ]
        read_only_fields = ["id", "creado_en", "actualizado_en"]

    def get_abogado_nombre(self, obj):
        if not obj.abogado_responsable:
            return None
        return obj.abogado_responsable.get_full_name() or obj.abogado_responsable.username

    def get_fecha_limite_subsanacion(self, obj):
        return limite_subsanacion(obj)

    def get_dias_para_subsanar(self, obj):
        limite = limite_subsanacion(obj)
        return (limite - timezone.localdate()).days if limite else None

    @staticmethod
    def _limpiar(value, campo):
        value = " ".join(value.split())
        if len(value) < 3:
            raise serializers.ValidationError(f"Escriba el nombre del {campo} (mínimo 3 caracteres).")
        return value

    def validate_clase_proceso(self, value):
        value = " ".join(value.split())
        if len(value) < 3:
            raise serializers.ValidationError("Indique la clase de proceso (por ejemplo, Ejecutivo singular).")
        return value

    def validate_demandante(self, value):
        return self._limpiar(value, "demandante")

    def validate_demandado(self, value):
        return self._limpiar(value, "demandado")

    def validate_pretensiones(self, value):
        value = value.strip()
        if len(value) < 10:
            raise serializers.ValidationError("Describa las pretensiones (mínimo 10 caracteres).")
        return value

    def validate_cuantia(self, value):
        if value < 0:
            raise serializers.ValidationError("La cuantía no puede ser negativa.")
        return value

    def validate_expediente(self, value):
        exigir_expediente_visible(self.context.get("request"), value)
        return value

    def validate_abogado_responsable(self, value):
        request = self.context.get("request")
        if value is not None and request is not None and not es_directivo(request.user) and value != request.user:
            raise serializers.ValidationError("Solo un administrador o socio puede asignar la demanda a otro abogado.")
        return value

    def validate(self, attrs):
        def valor(campo):
            if campo in attrs:
                return attrs[campo]
            return getattr(self.instance, campo, None) if self.instance else None

        estado = valor("estado") or Demanda.Estado.ELABORACION
        radicacion = valor("fecha_radicacion")
        inadmision = valor("fecha_inadmision")
        admision = valor("fecha_admision")
        hoy = timezone.localdate()
        errores = {}

        requieren_radicacion = {
            Demanda.Estado.RADICADA, Demanda.Estado.INADMITIDA, Demanda.Estado.ADMITIDA, Demanda.Estado.RECHAZADA,
        }
        if estado in requieren_radicacion and not radicacion:
            errores["fecha_radicacion"] = "Indique la fecha de radicación."
        if radicacion and radicacion > hoy:
            errores["fecha_radicacion"] = "La fecha de radicación no puede ser futura."
        if estado == Demanda.Estado.INADMITIDA:
            if not inadmision:
                errores["fecha_inadmision"] = "Indique la fecha del auto que inadmite la demanda."
            elif radicacion and inadmision < radicacion:
                errores["fecha_inadmision"] = "No puede ser anterior a la radicación."
        if estado == Demanda.Estado.ADMITIDA:
            if not admision:
                errores["fecha_admision"] = "Indique la fecha del auto admisorio."
            elif radicacion and admision < radicacion:
                errores["fecha_admision"] = "No puede ser anterior a la radicación."
        if errores:
            raise serializers.ValidationError(errores)
        return attrs


def _nombre(usuario):
    return (usuario.get_full_name() or usuario.username) if usuario else None


def _validar_abogado(request, value):
    if value is not None and request is not None and not es_directivo(request.user) and value != request.user:
        raise serializers.ValidationError("Solo un administrador o socio puede asignarlo a otro abogado.")
    return value


def _nombre_parte(value, campo):
    value = " ".join(value.split())
    if len(value) < 3:
        raise serializers.ValidationError(f"Escriba el nombre del {campo} (mínimo 3 caracteres).")
    return value


class ContestacionSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source="cliente.nombre", read_only=True, default=None)
    expediente_numero = serializers.CharField(source="expediente.numero", read_only=True, default=None)
    juzgado_nombre = serializers.CharField(source="juzgado.nombre", read_only=True, default=None)
    abogado_nombre = serializers.SerializerMethodField()
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    fecha_limite = serializers.SerializerMethodField()
    dias_restantes = serializers.SerializerMethodField()
    extemporanea = serializers.SerializerMethodField()

    class Meta:
        model = ContestacionDemanda
        fields = [
            "id", "clase_proceso", "demandante", "demandado", "cliente", "cliente_nombre", "expediente",
            "expediente_numero", "juzgado", "juzgado_nombre", "fecha_notificacion", "dias_termino",
            "fecha_limite", "dias_restantes", "estado", "estado_display", "fecha_presentacion", "extemporanea",
            "excepciones", "pruebas", "borrador", "abogado_responsable", "abogado_nombre", "observaciones",
            "creado_en", "actualizado_en",
        ]
        read_only_fields = ["id", "creado_en", "actualizado_en"]

    @staticmethod
    def limite(obj):
        if obj.fecha_notificacion:
            return sumar_dias_habiles(obj.fecha_notificacion, obj.dias_termino)
        return None

    def get_abogado_nombre(self, obj):
        return _nombre(obj.abogado_responsable)

    def get_fecha_limite(self, obj):
        return self.limite(obj)

    def get_dias_restantes(self, obj):
        limite = self.limite(obj)
        if limite is None or obj.estado in (ContestacionDemanda.Estado.PRESENTADA, ContestacionDemanda.Estado.NO_CONTESTADA):
            return None
        return (limite - timezone.localdate()).days

    def get_extemporanea(self, obj):
        limite = self.limite(obj)
        return bool(limite and obj.fecha_presentacion and obj.fecha_presentacion > limite)

    def validate_clase_proceso(self, value):
        value = " ".join(value.split())
        if len(value) < 3:
            raise serializers.ValidationError("Indique la clase de proceso.")
        return value

    def validate_demandante(self, value):
        return _nombre_parte(value, "demandante")

    def validate_demandado(self, value):
        return _nombre_parte(value, "demandado")

    def validate_dias_termino(self, value):
        if not 1 <= value <= 90:
            raise serializers.ValidationError("El término debe estar entre 1 y 90 días hábiles.")
        return value

    def validate_expediente(self, value):
        exigir_expediente_visible(self.context.get("request"), value)
        return value

    def validate_abogado_responsable(self, value):
        return _validar_abogado(self.context.get("request"), value)

    def validate(self, attrs):
        def valor(campo):
            if campo in attrs:
                return attrs[campo]
            return getattr(self.instance, campo, None) if self.instance else None

        hoy = timezone.localdate()
        notificacion = valor("fecha_notificacion")
        presentacion = valor("fecha_presentacion")
        estado = valor("estado") or ContestacionDemanda.Estado.POR_ELABORAR
        errores = {}
        if notificacion and notificacion > hoy:
            errores["fecha_notificacion"] = "La fecha de notificación no puede ser futura."
        if estado == ContestacionDemanda.Estado.PRESENTADA:
            if not presentacion:
                errores["fecha_presentacion"] = "Indique la fecha en que se presentó la contestación."
            elif presentacion > hoy:
                errores["fecha_presentacion"] = "La fecha de presentación no puede ser futura."
            elif notificacion and presentacion < notificacion:
                errores["fecha_presentacion"] = "No puede ser anterior a la notificación."
        if errores:
            raise serializers.ValidationError(errores)
        return attrs


DIAS_COMPARECENCIA = {"mismo_municipio": 5, "otro_municipio": 10, "exterior": 30}


class CitacionSerializer(serializers.ModelSerializer):
    expediente_numero = serializers.CharField(source="expediente.numero", read_only=True, default=None)
    demanda_texto = serializers.SerializerMethodField()
    abogado_nombre = serializers.SerializerMethodField()
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    ubicacion_display = serializers.CharField(source="get_ubicacion_display", read_only=True)
    fecha_limite_comparecencia = serializers.SerializerMethodField()
    dias_restantes = serializers.SerializerMethodField()
    fecha_surte_efecto = serializers.SerializerMethodField()

    class Meta:
        model = Citacion
        fields = [
            "id", "demanda", "demanda_texto", "expediente", "expediente_numero", "destinatario", "direccion",
            "tipo", "tipo_display", "ubicacion", "ubicacion_display", "estado", "estado_display", "fecha_envio",
            "empresa_mensajeria", "guia", "fecha_entrega", "fecha_notificacion", "fecha_limite_comparecencia",
            "dias_restantes", "fecha_surte_efecto", "abogado_responsable", "abogado_nombre", "observaciones",
            "creado_en", "actualizado_en",
        ]
        read_only_fields = ["id", "creado_en", "actualizado_en"]

    def get_demanda_texto(self, obj):
        return f"{obj.demanda.clase_proceso}: {obj.demanda.demandante} vs {obj.demanda.demandado}" if obj.demanda else None

    def get_abogado_nombre(self, obj):
        return _nombre(obj.abogado_responsable)

    @staticmethod
    def limite(obj):
        """Plazo del demandado para comparecer a notificarse (solo para citación del art. 291)."""
        if obj.tipo == Citacion.Tipo.CITACION and obj.fecha_entrega:
            return sumar_dias_habiles(obj.fecha_entrega, DIAS_COMPARECENCIA[obj.ubicacion])
        return None

    def get_fecha_limite_comparecencia(self, obj):
        return self.limite(obj)

    def get_dias_restantes(self, obj):
        limite = self.limite(obj)
        if limite is None or obj.estado == Citacion.Estado.NOTIFICADO:
            return None
        return (limite - timezone.localdate()).days

    def get_fecha_surte_efecto(self, obj):
        """Notificación por aviso: se considera surtida al finalizar el día hábil siguiente a la entrega."""
        if obj.tipo == Citacion.Tipo.AVISO and obj.fecha_entrega:
            return sumar_dias_habiles(obj.fecha_entrega, 1)
        return None

    def validate_destinatario(self, value):
        return _nombre_parte(value, "destinatario")

    def validate_expediente(self, value):
        exigir_expediente_visible(self.context.get("request"), value)
        return value

    def validate_abogado_responsable(self, value):
        return _validar_abogado(self.context.get("request"), value)

    def validate(self, attrs):
        def valor(campo):
            if campo in attrs:
                return attrs[campo]
            return getattr(self.instance, campo, None) if self.instance else None

        hoy = timezone.localdate()
        estado = valor("estado") or Citacion.Estado.PENDIENTE
        envio = valor("fecha_envio")
        entrega = valor("fecha_entrega")
        notificacion = valor("fecha_notificacion")
        errores = {}
        if estado != Citacion.Estado.PENDIENTE and not envio:
            errores["fecha_envio"] = "Indique la fecha de envío."
        if envio and envio > hoy:
            errores["fecha_envio"] = "La fecha de envío no puede ser futura."
        if estado == Citacion.Estado.ENTREGADA and not entrega:
            errores["fecha_entrega"] = "Indique la fecha de entrega."
        if entrega:
            if entrega > hoy:
                errores["fecha_entrega"] = "La fecha de entrega no puede ser futura."
            elif envio and entrega < envio:
                errores["fecha_entrega"] = "No puede ser anterior al envío."
        if estado == Citacion.Estado.NOTIFICADO:
            if not notificacion:
                errores["fecha_notificacion"] = "Indique la fecha en que se notificó."
            elif notificacion > hoy:
                errores["fecha_notificacion"] = "La fecha de notificación no puede ser futura."
        if errores:
            raise serializers.ValidationError(errores)
        return attrs
