"""Envío de correo por la API HTTPS de Resend (https://resend.com).

Se usa porque los servicios gratuitos de Render bloquean el SMTP saliente
(puertos 25, 465 y 587). Solo requiere la variable de entorno RESEND_API_KEY.
Nota: con una cuenta gratuita sin dominio verificado, Resend solo entrega
correos a la dirección con la que se registró la cuenta.
"""
import json
import logging
import urllib.error
import urllib.request

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)


class ResendEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        enviados = 0
        for mensaje in email_messages:
            datos = json.dumps(
                {
                    "from": mensaje.from_email,
                    "to": list(mensaje.to),
                    "subject": mensaje.subject,
                    "text": mensaje.body,
                }
            ).encode("utf-8")
            peticion = urllib.request.Request(
                "https://api.resend.com/emails",
                data=datos,
                method="POST",
                headers={
                    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                    "Content-Type": "application/json",
                    "User-Agent": "lexerp/1.0",
                },
            )
            try:
                with urllib.request.urlopen(peticion, timeout=10) as respuesta:
                    if 200 <= respuesta.status < 300:
                        enviados += 1
            except (urllib.error.URLError, OSError):
                logger.exception("Resend no pudo enviar el correo a %s", mensaje.to)
                if not self.fail_silently:
                    raise
        return enviados
