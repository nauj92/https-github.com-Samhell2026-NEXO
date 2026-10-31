from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AutorizarDatosView,
    CambiarPasswordView,
    ConfirmarRecuperacionView,
    PerfilView,
    SolicitarRecuperacionView,
    UsuarioAdminViewSet,
    UsuarioListView,
)

router = DefaultRouter()
router.register(r"gestion-usuarios", UsuarioAdminViewSet, basename="gestion-usuarios")

urlpatterns = [
    path("perfil/", PerfilView.as_view(), name="perfil"),
    path("perfil/cambiar-password/", CambiarPasswordView.as_view(), name="cambiar-password"),
    path("perfil/autorizar-datos/", AutorizarDatosView.as_view(), name="autorizar-datos"),
    path("usuarios/", UsuarioListView.as_view(), name="usuarios-list"),
    path("password-reset/", SolicitarRecuperacionView.as_view(), name="password-reset"),
    path("password-reset/confirmar/", ConfirmarRecuperacionView.as_view(), name="password-reset-confirmar"),
] + router.urls
