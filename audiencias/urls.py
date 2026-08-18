from rest_framework.routers import DefaultRouter
from .views import AudienciaViewSet

router = DefaultRouter()
router.register(r"audiencias", AudienciaViewSet)

urlpatterns = router.urls