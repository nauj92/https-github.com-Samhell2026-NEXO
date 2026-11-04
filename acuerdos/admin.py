from django.contrib import admin

from .models import AcuerdoPago, CuotaAcuerdo


class CuotaInline(admin.TabularInline):
    model = CuotaAcuerdo
    extra = 0


@admin.register(AcuerdoPago)
class AcuerdoPagoAdmin(admin.ModelAdmin):
    list_display = ("concepto", "expediente", "deudor", "valor_total", "estado", "fecha_acuerdo")
    list_filter = ("estado",)
    search_fields = ("concepto", "deudor", "expediente__numero")
    inlines = [CuotaInline]
