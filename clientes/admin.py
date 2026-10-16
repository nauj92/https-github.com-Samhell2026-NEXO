from django.contrib import admin
from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "numero_documento", "telefono", "email")
    search_fields = ("nombre", "numero_documento")
