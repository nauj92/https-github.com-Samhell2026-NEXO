from django.contrib import admin
from .models import DocumentoExpediente, EtapaProceso, Expediente, Juzgado


@admin.register(Juzgado)
class JuzgadoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "ciudad", "materia")
    search_fields = ("nombre", "ciudad")


class EtapaProcesoInline(admin.TabularInline):
    model = EtapaProceso
    extra = 1


@admin.register(Expediente)
class ExpedienteAdmin(admin.ModelAdmin):
    list_display = ("numero", "cliente", "demandante", "demandado", "estado", "abogado_asignado", "juzgado")
    list_filter = ("estado", "materia", "juzgado")
    search_fields = ("numero", "demandante", "demandado")
    inlines = [EtapaProcesoInline]


@admin.register(EtapaProceso)
class EtapaProcesoAdmin(admin.ModelAdmin):
    list_display = ("expediente", "nombre", "estado", "fecha_limite", "orden")
    list_filter = ("estado",)


@admin.register(DocumentoExpediente)
class DocumentoExpedienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "expediente", "tamano", "subido_por", "subido_en")
    search_fields = ("nombre", "expediente__numero")
    readonly_fields = ("tamano", "subido_por", "subido_en")
    exclude = ("contenido",)
