from rest_framework.routers import DefaultRouter

from .views import AcuerdoPagoViewSet

router = DefaultRouter()
router.register(r"acuerdos-pago", AcuerdoPagoViewSet, basename="acuerdo-pago")

urlpatterns = router.urls
