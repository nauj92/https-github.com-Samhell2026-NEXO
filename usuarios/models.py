from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    class Rol(models.TextChoices):
        # Orden de permisos: Cliente < Dependiente < Escribiente < Secretaria < Abogado < Administrador
        ADMINISTRADOR = "administrador", "Administrador"
        ABOGADO = "abogado", "Abogado"
        SECRETARIO = "secretario_juridico", "Secretaria"
        ESCRIBIENTE = "escribiente", "Escribiente"
        DEPENDIENTE = "dependiente", "Dependiente"
        CLIENTE = "cliente", "Cliente"

    rol = models.CharField(max_length=30, choices=Rol.choices, default=Rol.ABOGADO)
    # El socio es un abogado que ve todos los expedientes del despacho (no es un rol aparte).
    es_socio = models.BooleanField("socio", default=False, help_text="Solo para abogados: ve todos los expedientes.")
    telefono = models.CharField(max_length=20, blank=True)
    cedula = models.CharField("cédula", max_length=12, blank=True)
    tarjeta_profesional = models.CharField("tarjeta profesional", max_length=15, blank=True)
    # Solo para el rol Cliente: la ficha de cliente cuyo proceso puede consultar en el portal.
    cliente = models.ForeignKey(
        "clientes.Cliente", on_delete=models.SET_NULL, null=True, blank=True, related_name="usuarios_portal",
        help_text="Solo para usuarios con rol Cliente: ficha del cliente que verá en el portal.",
    )

    # Primer ingreso: el administrador crea la cuenta con una contraseña temporal; la persona debe cambiarla
    # y autorizar el tratamiento de sus datos personales antes de usar el sistema.
    debe_cambiar_password = models.BooleanField(default=False)
    autorizacion_datos_pendiente = models.BooleanField(default=False)
    fecha_autorizacion_datos = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_rol_display()})"

# Create your models here.
