from django.urls import path

from .dashboard import DashboardResumenView
from .views import CalcularPlazoView

urlpatterns = [
    path("dashboard/resumen/", DashboardResumenView.as_view(), name="dashboard-resumen"),
    path("plazos/calcular/", CalcularPlazoView.as_view(), name="plazos-calcular"),
]
