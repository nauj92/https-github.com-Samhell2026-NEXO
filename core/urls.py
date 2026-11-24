from django.urls import path

from .auditoria import AuditoriaView
from .dashboard import DashboardResumenView
from .views import CalcularPlazoView

urlpatterns = [
    path("dashboard/resumen/", DashboardResumenView.as_view(), name="dashboard-resumen"),
    path("auditoria/", AuditoriaView.as_view(), name="auditoria"),
    path("plazos/calcular/", CalcularPlazoView.as_view(), name="plazos-calcular"),
]
