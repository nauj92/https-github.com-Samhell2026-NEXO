"""Correos de la gestión de usuarios."""
import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def enviar_bienvenida(usuario, password_temporal):
    """Avisa a la persona que el administrador creó su cuenta. Devuelve True si el correo salió.

    Nunca lanza: si el correo falla, la cuenta queda creada y el administrador lo ve en la respuesta.
    """
    enlace = f"{settings.FRONTEND_URL.rstrip('/')}/login"
    cuerpo = (
        f"Hola {usuario.get_full_name() or usuario.username},\n\n"
        f"El administrador de Lex-ERP creó su cuenta con el rol de {usuario.get_rol_display()}.\n\n"
        f"  Dirección de ingreso: {enlace}\n"
        f"  Usuario: {usuario.username}\n"
        f"  Contraseña temporal: {password_temporal}\n\n"
        "Al ingresar por primera vez el sistema le pedirá:\n"
        "  1. Cambiar la contraseña temporal por una propia.\n"
        "  2. Leer y autorizar el tratamiento de sus datos personales.\n\n"
        "Por seguridad no comparta esta contraseña. Si usted no esperaba este mensaje, avise al administrador."
    )
    try:
        send_mail("Su cuenta en Lex-ERP fue creada", cuerpo, settings.DEFAULT_FROM_EMAIL, [usuario.email])
        return True
    except Exception:
        logger.exception("No se pudo enviar el correo de bienvenida a %s", usuario.username)
        return False
