from django.contrib import admin
from .models import Audiencia


@admin.register(Audiencia)
class AudienciaAdmin(admin.ModelAdmin):
    list_display = ("expediente", "fecha_hora", "lugar")
    list_filter = ("fecha_hora",)
    search_fields = ("expediente__numero", "lugar")