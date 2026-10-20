from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import DashboardStatsView, EtapaProcesoViewSet, ExpedienteViewSet, JuzgadoViewSet

router = DefaultRouter()
router.register(r"juzgados", JuzgadoViewSet, basename="juzgado")
router.register(r"expedientes", ExpedienteViewSet, basename="expediente")
router.register(r"etapas", EtapaProcesoViewSet, basename="etapa")

urlpatterns = router.urls + [
    path("dashboard/stats/", DashboardStatsView.as_view(), name="dashboard-stats"),
]
