from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import JuzgadoViewSet, ExpedienteViewSet, EtapaProcesoViewSet, DashboardStatsView

router = DefaultRouter()
router.register(r"juzgados", JuzgadoViewSet)
router.register(r"expedientes", ExpedienteViewSet, basename="expediente")
router.register(r"etapas", EtapaProcesoViewSet)

urlpatterns = router.urls + [
    path("dashboard/stats/", DashboardStatsView.as_view(), name="dashboard-stats"),
]