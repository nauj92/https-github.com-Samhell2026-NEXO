from rest_framework.routers import DefaultRouter

from .views import LiquidacionViewSet

router = DefaultRouter()
router.register(r"liquidaciones", LiquidacionViewSet, basename="liquidacion")

urlpatterns = router.urls
