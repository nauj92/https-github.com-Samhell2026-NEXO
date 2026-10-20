from rest_framework.routers import DefaultRouter

from .views import VigilanciaViewSet

router = DefaultRouter()
router.register(r"vigilancia", VigilanciaViewSet, basename="vigilancia")

urlpatterns = router.urls
