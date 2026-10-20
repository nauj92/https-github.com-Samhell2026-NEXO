from django.urls import path

from .views import CalcularPlazoView

urlpatterns = [
    path("plazos/calcular/", CalcularPlazoView.as_view(), name="plazos-calcular"),
]
