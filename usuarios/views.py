import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from core.permisos import EsAdministrador, EsDirectivo

from .correos import enviar_bienvenida
from .serializers import (
    CambiarPasswordSerializer,
    ConfirmarRecuperacionSerializer,
    PerfilSerializer,
    SolicitudRecuperacionSerializer,
    UsuarioAdminSerializer,
    UsuarioSimpleSerializer,
    desbloquear_acceso,
)

Usuario = get_user_model()
logger = logging.getLogger(__name__)


class PerfilView(APIView):
    permitido_en_primer_ingreso = True

    def get(self, request):
        serializer = PerfilSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = PerfilSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class CambiarPasswordView(APIView):
    permitido_en_primer_ingreso = True

    def post(self, request):
        serializer = CambiarPasswordSerializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)

        usuario = request.user
        password_actual = serializer.validated_data["password_actual"]
        password_nueva = serializer.validated_data["password_nueva"]

        if not usuario.check_password(password_actual):
            return Response({"detail": "La contraseña actual no es correcta."}, status=status.HTTP_400_BAD_REQUEST)

        usuario.set_password(password_nueva)
        usuario.debe_cambiar_password = False
        usuario.save()
        return Response({"detail": "Contraseña actualizada correctamente."})


class AutorizarDatosView(APIView):
    """POST {acepto: true}. Registra la autorización para el tratamiento de datos personales."""

    permitido_en_primer_ingreso = True

    def post(self, request):
        if request.data.get("acepto") is not True:
            return Response(
                {"detail": "Debe aceptar la autorización para continuar."}, status=status.HTTP_400_BAD_REQUEST
            )
        usuario = request.user
        usuario.autorizacion_datos_pendiente = False
        usuario.fecha_autorizacion_datos = timezone.now()
        usuario.save(update_fields=["autorizacion_datos_pendiente", "fecha_autorizacion_datos"])
        return Response({"detail": "Autorización registrada."})


class UsuarioListView(APIView):
    """Lista simple de usuarios activos, para asignar abogados a los expedientes."""

    def get(self, request):
        usuarios = Usuario.objects.filter(
            is_active=True, rol__in=["abogado", "socio_director", "administrador"]
        ).order_by("first_name", "username")
        serializer = UsuarioSimpleSerializer(usuarios, many=True)
        return Response(serializer.data)


class UsuarioAdminViewSet(viewsets.ModelViewSet):
    """Gestión de usuarios. Administradores y socios consultan; solo el administrador crea y modifica.

    No se borran: se desactivan. Al crear una cuenta se envía un correo de bienvenida.
    """

    serializer_class = UsuarioAdminSerializer
    queryset = Usuario.objects.all().order_by("first_name", "username")
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [EsDirectivo()]
        return [EsAdministrador()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = serializer.save()
        enviado = enviar_bienvenida(usuario, request.data.get("password", ""))
        return Response({**serializer.data, "correo_enviado": enviado}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def desbloquear(self, request, pk=None):
        """Quita el bloqueo por intentos fallidos de inicio de sesión."""
        usuario = self.get_object()
        if not desbloquear_acceso(usuario):
            return Response(
                {"detail": "No se pudo desbloquear el acceso. Revise el registro del servidor."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response({"detail": f"Se desbloqueó el acceso de {usuario.username}."})


# ---- Recuperación de contraseña ------------------------------------------------

MENSAJE_RECUPERACION = (
    "Si el correo está registrado, recibirá un mensaje con las instrucciones para restablecer su contraseña."
)


class RecuperacionThrottle(AnonRateThrottle):
    scope = "recuperacion"


class SolicitarRecuperacionView(APIView):
    """POST {email}. Responde siempre lo mismo, exista o no el correo (evita revelar quién tiene cuenta)."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [RecuperacionThrottle]

    def post(self, request):
        serializer = SolicitudRecuperacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        for usuario in Usuario.objects.filter(email__iexact=email, is_active=True):
            uid = urlsafe_base64_encode(force_bytes(usuario.pk))
            token = default_token_generator.make_token(usuario)
            enlace = f"{settings.FRONTEND_URL.rstrip('/')}/restablecer/{uid}/{token}"
            cuerpo = (
                f"Hola {usuario.get_full_name() or usuario.username},\n\n"
                "Recibimos una solicitud para restablecer la contraseña de su cuenta en Lex-ERP.\n"
                f"Use este enlace (vale {settings.PASSWORD_RESET_TIMEOUT // 60} minutos):\n\n{enlace}\n\n"
                "Si usted no lo solicitó, ignore este mensaje: su contraseña no cambiará."
            )
            try:
                send_mail("Restablecer contraseña - Lex-ERP", cuerpo, settings.DEFAULT_FROM_EMAIL, [usuario.email])
            except Exception:
                # No se revela el fallo al solicitante; queda en el registro del servidor.
                logger.exception("No se pudo enviar el correo de recuperación a %s", usuario.username)
        return Response({"detail": MENSAJE_RECUPERACION})


class ConfirmarRecuperacionView(APIView):
    """POST {uid, token, password_nueva}. Cambia la contraseña si el enlace es válido."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [RecuperacionThrottle]

    def post(self, request):
        serializer = ConfirmarRecuperacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        invalido = Response(
            {"detail": "El enlace no es válido o ya venció. Solicite uno nuevo."},
            status=status.HTTP_400_BAD_REQUEST,
        )
        try:
            usuario = Usuario.objects.get(pk=force_str(urlsafe_base64_decode(datos["uid"])), is_active=True)
        except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
            return invalido
        if not default_token_generator.check_token(usuario, datos["token"]):
            return invalido

        try:
            validate_password(datos["password_nueva"], user=usuario)
        except DjangoValidationError as exc:
            return Response({"password_nueva": list(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)

        usuario.set_password(datos["password_nueva"])
        usuario.save()
        desbloquear_acceso(usuario)
        return Response({"detail": "Contraseña actualizada. Ya puede iniciar sesión."})
