from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from core.testutils import crear_expediente, crear_usuario
from notificaciones.models import Notificacion

from .models import Tarea


class TareasTests(APITestCase):
    def setUp(self):
        self.admin = crear_usuario("adm", "administrador")
        self.abogado = crear_usuario("abo", "abogado")
        self.otro_abogado = crear_usuario("abo2", "abogado")
        self.secretaria = crear_usuario("sec", "secretario_juridico")
        self.escribiente = crear_usuario("esc", "escribiente")
        self.dependiente = crear_usuario("dep", "dependiente")
        self.otro_dependiente = crear_usuario("dep2", "dependiente")
        self.cliente = crear_usuario("cli", "cliente")
        self.exp = crear_expediente(self.abogado)
        self.exp.colaboradores.add(self.secretaria)

    def como(self, usuario):
        self.client.force_authenticate(usuario)

    def crear(self, **extra):
        datos = {"titulo": "Radicar memorial", "tipo": "presentar_escrito", "asignado_a": self.dependiente.pk,
                 "expediente": self.exp.pk}
        datos.update(extra)
        return self.client.post("/api/tareas/", datos, format="json")

    def test_abogado_crea_y_el_dependiente_recibe_aviso(self):
        self.como(self.abogado)
        r = self.crear()
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["creado_por"], self.abogado.pk)
        self.assertTrue(Notificacion.objects.filter(usuario=self.dependiente, tipo="tarea").exists())

    def test_dependiente_no_crea_ni_elimina(self):
        self.como(self.abogado)
        tarea_id = self.crear().data["id"]
        self.como(self.dependiente)
        self.assertEqual(self.crear().status_code, 403)
        self.assertEqual(self.client.delete(f"/api/tareas/{tarea_id}/").status_code, 403)

    def test_dependiente_solo_ve_sus_tareas(self):
        self.como(self.abogado)
        self.crear()
        self.crear(asignado_a=self.otro_dependiente.pk, titulo="Otra")
        self.como(self.dependiente)
        r = self.client.get("/api/tareas/")
        self.assertEqual([t["titulo"] for t in r.data], ["Radicar memorial"])

    def test_cliente_sin_acceso(self):
        self.como(self.cliente)
        self.assertEqual(self.client.get("/api/tareas/").status_code, 403)

    def test_no_se_asigna_a_clientes(self):
        self.como(self.abogado)
        r = self.crear(asignado_a=self.cliente.pk)
        self.assertEqual(r.status_code, 400)

    def test_no_se_vincula_expediente_ajeno(self):
        ajeno = crear_expediente(self.otro_abogado)
        self.como(self.abogado)
        self.assertEqual(self.crear(expediente=ajeno.pk).status_code, 400)

    def test_dependiente_marca_realizada_y_avisa_al_creador(self):
        self.como(self.abogado)
        tarea_id = self.crear().data["id"]
        self.como(self.dependiente)
        r = self.client.patch(
            f"/api/tareas/{tarea_id}/", {"estado": "realizada", "observacion_cierre": "Radicado"}, format="json"
        )
        self.assertEqual(r.status_code, 200, r.data)
        tarea = Tarea.objects.get(pk=tarea_id)
        self.assertEqual(tarea.estado, "realizada")
        self.assertIsNotNone(tarea.fecha_realizada)
        self.assertTrue(Notificacion.objects.filter(usuario=self.abogado, tipo="tarea").exists())

    def test_dependiente_no_cambia_otros_campos(self):
        self.como(self.abogado)
        tarea_id = self.crear().data["id"]
        self.como(self.dependiente)
        r = self.client.patch(f"/api/tareas/{tarea_id}/", {"titulo": "Cambiado"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_dependiente_ajeno_no_ve_ni_modifica(self):
        self.como(self.abogado)
        tarea_id = self.crear().data["id"]
        self.como(self.otro_dependiente)
        self.assertEqual(self.client.patch(f"/api/tareas/{tarea_id}/", {"estado": "realizada"}, format="json").status_code, 404)

    def test_comprobante_subir_descargar_y_borrar(self):
        self.como(self.abogado)
        tarea_id = self.crear().data["id"]
        self.como(self.dependiente)
        archivo = SimpleUploadedFile("cargo.pdf", b"%PDF-1.4 prueba", content_type="application/pdf")
        r = self.client.post(f"/api/tareas/{tarea_id}/comprobantes/", {"archivo": archivo}, format="multipart")
        self.assertEqual(r.status_code, 201, r.data)
        comprobante_id = r.data["comprobantes"][0]["id"]
        d = self.client.get(f"/api/tareas/{tarea_id}/comprobantes/{comprobante_id}/")
        self.assertEqual(d.status_code, 200)
        self.assertEqual(d.content, b"%PDF-1.4 prueba")
        self.assertEqual(self.client.delete(f"/api/tareas/{tarea_id}/comprobantes/{comprobante_id}/").status_code, 204)

    def test_comprobante_rechaza_extension_no_permitida(self):
        self.como(self.abogado)
        tarea_id = self.crear().data["id"]
        self.como(self.dependiente)
        archivo = SimpleUploadedFile("virus.exe", b"MZ", content_type="application/octet-stream")
        r = self.client.post(f"/api/tareas/{tarea_id}/comprobantes/", {"archivo": archivo}, format="multipart")
        self.assertEqual(r.status_code, 400)

    def test_secretaria_ve_tareas_de_sus_expedientes(self):
        self.como(self.abogado)
        self.crear()
        self.como(self.secretaria)
        self.assertEqual(len(self.client.get("/api/tareas/").data), 1)
        self.como(self.escribiente)
        self.assertEqual(len(self.client.get("/api/tareas/").data), 0)
