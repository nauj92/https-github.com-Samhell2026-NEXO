from django.contrib import admin

from .models import Mensaje


@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    list_display = ("expediente", "autor", "de_cliente", "creado_en")
    list_filter = ("de_cliente",)
