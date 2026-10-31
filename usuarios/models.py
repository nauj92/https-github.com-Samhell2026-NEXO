from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    class Rol(models.TextChoices):
        ADMINISTRADOR = "administrador", "Administrador"
        SOCIO_DIRECTOR = "socio_director", "Socio Director"
        ABOGADO = "abogado", "Abogado"
        SECRETARIO = "secretario_juridico", "Secretario(a) Jurídico"
        ESCRIBIENTE = "escribiente", "Escribiente"
        CLIENTE = "cliente", "Cliente"

    rol = models.CharField(max_length=30, choices=Rol.choices, default=Rol.ABOGADO)
    telefono = models.CharField(max_length=20, blank=True)
    cedula = models.CharField("cédula", max_length=12, blank=True)
    tarjeta_profesional = models.CharField("tarjeta profesional", max_length=15, blank=True)

    # Primer ingreso: el administrador crea la cuenta con una contraseña temporal; la persona debe cambiarla
    # y autorizar el tratamiento de sus datos personales antes de usar el sistema.
    debe_cambiar_password = models.BooleanField(default=False)
    autorizacion_datos_pendiente = models.BooleanField(default=False)
    fecha_autorizacion_datos = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_rol_display()})"

# Create your models here.
