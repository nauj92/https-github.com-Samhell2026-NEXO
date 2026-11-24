from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from rest_framework.test import APITestCase

from core.testutils import crear_cliente, crear_expediente, crear_usuario
from expedientes.models import DocumentoExpediente
from notificaciones.models import Notificacion

from .models import Mensaje


class PortalTests(APITestCase):
    def setUp(self):
        self.abogado = crear_usuario("abo", "abogado")
        self.otro_abogado = crear_usuario("abo2", "abogado")
        self.admin = crear_usuario("adm", "administrador")
        self.secretaria = crear_usuario("sec", "secretario_juridico")
        self.cliente = crear_cliente("Cliente Uno")
        self.cliente.email = "cliente1@example.com"
        self.cliente.save()
        self.otro_cliente = crear_cliente("Cliente Dos")
        self.usuario = crear_usuario("cli", "cliente", cliente=self.cliente)
        self.sin_vinculo = crear_usuario("cli2", "cliente")
        self.exp = crear_expediente(self.abogado, cliente=self.cliente)
        self.exp.colaboradores.add(self.secretaria)
        self.ajeno = crear_expediente(self.abogado, cliente=self.otro_cliente)
        self.doc = self.subir_documento(self.exp, "interno.pdf")

    def subir_documento(self, exp, nombre, **extra):
        return DocumentoExpediente.objects.create(
            expediente=exp, nombre=nombre, tamano=4, contenido=b"data", subido_por=self.abogado, **extra
        )

    def como(self, usuario):
        self.client.force_authenticate(usuario)

    def test_cliente_solo_ve_sus_expedientes(self):
        self.como(self.usuario)
        r = self.client.get("/api/portal/expedientes/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual([e["numero"] for e in r.data], [self.exp.numero])
        self.assertNotIn("abogado_asignado", r.data[0])

    def test_cliente_sin_vinculo_o_personal_no_entra(self):
        self.como(self.sin_vinculo)
        self.assertEqual(self.client.get("/api/portal/expedientes/").status_code, 403)
        self.como(self.abogado)
        self.assertEqual(self.client.get("/api/portal/expedientes/").status_code, 403)

    def test_cliente_no_entra_al_resto_del_sistema(self):
        self.como(self.usuario)
        for ruta in ("/api/expedientes/", "/api/tareas/", "/api/mensajes/?expediente=1"):
            self.assertEqual(self.client.get(ruta).status_code, 403, ruta)

    def test_solo_ve_documentos_compartidos(self):
        self.como(self.usuario)
        self.assertEqual(self.client.get(f"/api/portal/expedientes/{self.exp.pk}/documentos/").data, [])
        self.assertEqual(self.client.get(f"/api/portal/expedientes/{self.exp.pk}/documentos/{self.doc.pk}/").status_code, 404)
        self.como(self.abogado)
        r = self.client.post(
            f"/api/expedientes/{self.exp.pk}/documentos/{self.doc.pk}/compartir/", {"compartido": True}, format="json"
        )
        self.assertEqual(r.status_code, 200, r.data)
        self.assertTrue(r.data["compartido_cliente"])
        self.como(self.usuario)
        lista = self.client.get(f"/api/portal/expedientes/{self.exp.pk}/documentos/").data
        self.assertEqual([d["nombre"] for d in lista], ["interno.pdf"])
        d = self.client.get(f"/api/portal/expedientes/{self.exp.pk}/documentos/{self.doc.pk}/")
        self.assertEqual(d.status_code, 200)
        self.assertEqual(d.content, b"data")

    def test_compartir_avisa_al_cliente_por_portal_y_correo(self):
        self.como(self.abogado)
        self.client.post(
            f"/api/expedientes/{self.exp.pk}/documentos/{self.doc.pk}/compartir/", {"compartido": True}, format="json"
        )
        self.assertTrue(Notificacion.objects.filter(usuario=self.usuario).exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["cliente1@example.com"])

    def test_solo_el_abogado_comparte(self):
        for usuario in (self.secretaria, self.admin):
            self.como(usuario)
            r = self.client.post(
                f"/api/expedientes/{self.exp.pk}/documentos/{self.doc.pk}/compartir/", {"compartido": True}, format="json"
            )
            self.assertEqual(r.status_code, 403, usuario.username)

    def test_no_ve_documentos_ni_expedientes_ajenos(self):
        self.como(self.usuario)
        self.assertEqual(self.client.get(f"/api/portal/expedientes/{self.ajeno.pk}/documentos/").status_code, 404)
        self.assertEqual(self.client.get(f"/api/portal/expedientes/{self.ajeno.pk}/mensajes/").status_code, 404)

    def test_cliente_sube_documento_y_avisa_al_abogado(self):
        self.como(self.usuario)
        archivo = SimpleUploadedFile("cedula.pdf", b"%PDF-1.4 x", content_type="application/pdf")
        r = self.client.post(f"/api/portal/expedientes/{self.exp.pk}/documentos/", {"archivo": archivo}, format="multipart")
        self.assertEqual(r.status_code, 201, r.data)
        doc = DocumentoExpediente.objects.get(pk=r.data["id"])
        self.assertTrue(doc.origen_cliente and doc.compartido_cliente)
        self.assertTrue(Notificacion.objects.filter(usuario=self.abogado).exists())
        self.assertTrue(Notificacion.objects.filter(usuario=self.secretaria).exists())

    def test_cliente_no_sube_extension_prohibida(self):
        self.como(self.usuario)
        archivo = SimpleUploadedFile("malo.exe", b"MZ")
        r = self.client.post(f"/api/portal/expedientes/{self.exp.pk}/documentos/", {"archivo": archivo}, format="multipart")
        self.assertEqual(r.status_code, 400)

    def test_mensajes_en_ambos_sentidos(self):
        self.como(self.usuario)
        r = self.client.post(f"/api/portal/expedientes/{self.exp.pk}/mensajes/", {"texto": "Hola, ¿cómo va?"}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertTrue(r.data["de_cliente"])
        self.assertTrue(Notificacion.objects.filter(usuario=self.abogado).exists())
        self.como(self.abogado)
        self.assertEqual(len(self.client.get(f"/api/mensajes/?expediente={self.exp.pk}").data), 1)
        r = self.client.post("/api/mensajes/", {"expediente": self.exp.pk, "texto": "Todo en orden"}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertFalse(r.data["de_cliente"])
        self.assertTrue(Notificacion.objects.filter(usuario=self.usuario).exists())
        self.como(self.usuario)
        self.assertEqual(len(self.client.get(f"/api/portal/expedientes/{self.exp.pk}/mensajes/").data), 2)
        self.assertEqual(Mensaje.objects.count(), 2)

    def test_mensaje_vacio_se_rechaza(self):
        self.como(self.usuario)
        r = self.client.post(f"/api/portal/expedientes/{self.exp.pk}/mensajes/", {"texto": "   "}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_abogado_ajeno_no_ve_los_mensajes(self):
        Mensaje.objects.create(expediente=self.exp, autor=self.usuario, de_cliente=True, texto="privado")
        self.como(self.otro_abogado)
        self.assertEqual(self.client.get(f"/api/mensajes/?expediente={self.exp.pk}").status_code, 404)

    def test_aprobar_un_escrito_avisa_al_cliente(self):
        self.como(self.secretaria)
        r = self.client.post(
            "/api/citaciones/",
            {"destinatario": "Luis Gómez", "expediente": self.exp.pk, "abogado_responsable": self.abogado.pk},
            format="json",
        )
        self.assertEqual(r.status_code, 201, r.data)
        self.client.post(f"/api/citaciones/{r.data['id']}/enviar/")
        self.como(self.abogado)
        self.client.post(f"/api/citaciones/{r.data['id']}/aprobar/")
        self.assertTrue(Notificacion.objects.filter(usuario=self.usuario, mensaje__contains="aprobó").exists())

    def test_perfil_del_cliente_trae_su_ficha(self):
        self.como(self.usuario)
        r = self.client.get("/api/perfil/")
        self.assertEqual(r.data["cliente"], self.cliente.pk)
        self.assertEqual(r.data["cliente_nombre"], "Cliente Uno")
        self.assertIn("portal", r.data["permisos"])

    def test_admin_vincula_usuario_cliente(self):
        self.como(self.admin)
        r = self.client.patch(f"/api/gestion-usuarios/{self.sin_vinculo.pk}/", {"cliente": self.cliente.pk}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["cliente_nombre"], "Cliente Uno")
        # un abogado no puede quedar vinculado a un cliente
        r = self.client.patch(f"/api/gestion-usuarios/{self.otro_abogado.pk}/", {"cliente": self.cliente.pk}, format="json")
        self.assertIsNone(r.data["cliente"])
