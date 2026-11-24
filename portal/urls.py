from django.urls import path

from . import views

urlpatterns = [
    path("portal/expedientes/", views.MisExpedientes.as_view(), name="portal-expedientes"),
    path("portal/facturas/", views.MisFacturas.as_view(), name="portal-facturas"),
    path("portal/expedientes/<int:pk>/documentos/", views.MisDocumentos.as_view(), name="portal-documentos"),
    path("portal/expedientes/<int:pk>/documentos/<int:doc_id>/", views.DescargarDocumento.as_view(), name="portal-documento"),
    path("portal/expedientes/<int:pk>/mensajes/", views.MisMensajes.as_view(), name="portal-mensajes"),
    path("mensajes/", views.MensajesDespacho.as_view(), name="mensajes-despacho"),
]
