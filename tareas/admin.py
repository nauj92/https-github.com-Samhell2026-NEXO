from django.contrib import admin

from .models import ComprobanteTarea, Tarea


class ComprobanteInline(admin.TabularInline):
    model = ComprobanteTarea
    extra = 0
    fields = ("nombre", "tamano", "subido_por", "subido_en")
    readonly_fields = fields
    can_delete = False


@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "tipo", "expediente", "asignado_a", "fecha_limite", "estado")
    list_filter = ("estado", "tipo")
    search_fields = ("titulo", "expediente__numero")
    inlines = [ComprobanteInline]
