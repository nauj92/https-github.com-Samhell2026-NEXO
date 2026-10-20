from django.contrib import admin

from .models import Liquidacion


@admin.register(Liquidacion)
class LiquidacionAdmin(admin.ModelAdmin):
    list_display = ("id", "tipo", "referencia", "total", "creado_por", "creado_en")
    list_filter = ("tipo",)
    search_fields = ("referencia",)
