from django.contrib import admin

from .models import ActuacionVigilancia, Vigilancia


class ActuacionInline(admin.TabularInline):
    model = ActuacionVigilancia
    extra = 0


@admin.register(Vigilancia)
class VigilanciaAdmin(admin.ModelAdmin):
    list_display = ("expediente", "activa", "dias_alerta", "creado_en")
    list_filter = ("activa",)
    search_fields = ("expediente__numero",)
    inlines = [ActuacionInline]
