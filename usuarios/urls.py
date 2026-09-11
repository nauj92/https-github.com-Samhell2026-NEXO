from django.urls import path
from .views import PerfilView, CambiarPasswordView, UsuarioListView

urlpatterns = [
    path("perfil/", PerfilView.as_view(), name="perfil"),
    path("perfil/cambiar-password/", CambiarPasswordView.as_view(), name="cambiar-password"),
    path("usuarios/", UsuarioListView.as_view(), name="usuarios-list"),
]