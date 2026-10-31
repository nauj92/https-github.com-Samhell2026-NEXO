from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Información adicional", {"fields": ("rol", "telefono", "cedula", "tarjeta_profesional", "debe_cambiar_password", "autorizacion_datos_pendiente", "fecha_autorizacion_datos")}),
    )
    list_display = ("username", "email", "rol", "is_staff")

# Register your models here.
