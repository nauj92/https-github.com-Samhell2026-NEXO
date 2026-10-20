from django.contrib import admin

from .models import Citacion, ContestacionDemanda, Demanda


@admin.register(Demanda)
class DemandaAdmin(admin.ModelAdmin):
    list_display = ("clase_proceso", "demandante", "demandado", "estado", "abogado_responsable", "creado_en")
    list_filter = ("estado",)
    search_fields = ("demandante", "demandado", "clase_proceso")


@admin.register(ContestacionDemanda)
class ContestacionAdmin(admin.ModelAdmin):
    list_display = ("demandante", "demandado", "estado", "fecha_notificacion", "abogado_responsable")
    list_filter = ("estado",)


@admin.register(Citacion)
class CitacionAdmin(admin.ModelAdmin):
    list_display = ("destinatario", "tipo", "estado", "fecha_envio", "fecha_entrega")
    list_filter = ("tipo", "estado")
