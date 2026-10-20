from rest_framework.routers import DefaultRouter

from .views import CitacionViewSet, ContestacionViewSet, DemandaViewSet

router = DefaultRouter()
router.register(r"demandas", DemandaViewSet, basename="demanda")
router.register(r"contestaciones", ContestacionViewSet, basename="contestacion")
router.register(r"citaciones", CitacionViewSet, basename="citacion")

urlpatterns = router.urls
