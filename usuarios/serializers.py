import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

Usuario = get_user_model()


def desbloquear_acceso(usuario):
    """Reinicia los intentos fallidos de inicio de sesión (django-axes) de un usuario.

    Devuelve True si se pudo hacer. Nunca lanza: si axes cambia su API no debe romper el flujo principal.
    """
    try:
        from axes.utils import reset

        reset(username=usuario.username)
        return True
    except Exception:
        logging.getLogger(__name__).exception("No se pudo reiniciar el bloqueo de axes de %s", usuario.username)
        return False


class PerfilSerializer(serializers.ModelSerializer):
    es_directivo = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ["id", "username", "email", "first_name", "last_name", "telefono", "rol", "es_directivo"]
        read_only_fields = ["id", "username", "rol", "es_directivo"]

    def get_es_directivo(self, obj):
        from core.permisos import es_directivo

        return es_directivo(obj)


class CambiarPasswordSerializer(serializers.Serializer):
    password_actual = serializers.CharField(write_only=True)
    password_nueva = serializers.CharField(write_only=True)

    def validate_password_nueva(self, value):
        validate_password(value, user=self.context.get("user"))
        return value


class UsuarioSimpleSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ["id", "username", "nombre_completo", "rol", "email", "cedula", "tarjeta_profesional"]

    def get_nombre_completo(self, obj):
        nombre = obj.get_full_name()
        return nombre if nombre else obj.username


class UsuarioAdminSerializer(serializers.ModelSerializer):
    """Gestión de usuarios por administradores y socios."""

    password = serializers.CharField(write_only=True, required=False, style={"input_type": "password"})
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            "id", "username", "first_name", "last_name", "email", "telefono", "cedula", "tarjeta_profesional",
            "rol", "is_active", "password", "nombre_completo", "last_login",
        ]
        read_only_fields = ["id", "last_login"]
        extra_kwargs = {
            "email": {"required": True, "allow_blank": False},
            "first_name": {"required": True, "allow_blank": False},
            "last_name": {"required": True, "allow_blank": False},
        }

    def get_nombre_completo(self, obj):
        return obj.get_full_name() or obj.username

    def validate_username(self, value):
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError("El usuario debe tener al menos 3 caracteres.")
        return value

    def validate_cedula(self, value):
        limpio = "".join(value.split()).replace(".", "")
        if limpio and not (limpio.isdigit() and 5 <= len(limpio) <= 12):
            raise serializers.ValidationError("La cédula debe tener entre 5 y 12 dígitos, sin letras.")
        return limpio

    def validate_tarjeta_profesional(self, value):
        limpio = "".join(value.split()).replace(".", "")
        if limpio and not (limpio.isalnum() and 3 <= len(limpio) <= 15):
            raise serializers.ValidationError("La tarjeta profesional debe tener entre 3 y 15 letras o números.")
        return limpio

    def validate(self, attrs):
        inst = self.instance
        password = attrs.get("password")
        if inst is None and not password:
            raise serializers.ValidationError({"password": "La contraseña es obligatoria al crear un usuario."})

        if password:
            referencia = Usuario(
                username=attrs.get("username", inst.username if inst else ""),
                email=attrs.get("email", inst.email if inst else ""),
                first_name=attrs.get("first_name", inst.first_name if inst else ""),
                last_name=attrs.get("last_name", inst.last_name if inst else ""),
            )
            try:
                validate_password(password, user=referencia)
            except Exception as exc:  # django ValidationError con varios mensajes
                raise serializers.ValidationError({"password": list(getattr(exc, "messages", [str(exc)]))})

        # Evitar que un administrador se bloquee a sí mismo
        request = self.context.get("request")
        if inst is not None and request is not None and inst.pk == request.user.pk:
            if attrs.get("is_active") is False:
                raise serializers.ValidationError({"is_active": "No puede desactivar su propia cuenta."})
            if "rol" in attrs and attrs["rol"] != inst.rol:
                raise serializers.ValidationError({"rol": "No puede cambiar su propio rol."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        usuario = Usuario(**validated_data)
        usuario.set_password(password)
        usuario.save()
        return usuario

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for campo, valor in validated_data.items():
            setattr(instance, campo, valor)
        if password:
            instance.set_password(password)
        instance.save()
        if password:
            desbloquear_acceso(instance)
        return instance


class SolicitudRecuperacionSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ConfirmarRecuperacionSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password_nueva = serializers.CharField(write_only=True)
