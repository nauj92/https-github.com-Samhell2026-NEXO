from django.contrib import admin
from .models import Factura


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ("numero", "cliente", "monto", "estado", "fecha_emision", "fecha_vencimiento")
    list_filter = ("estado",)
    search_fields = ("numero", "cliente")