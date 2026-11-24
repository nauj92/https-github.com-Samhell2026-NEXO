from rest_framework.test import APITestCase

from core.testutils import crear_expediente, crear_usuario


class AuditoriaTests(APITestCase):
    def setUp(self):
        self.admin = crear_usuario("adm", "administrador")
        self.abogado = crear_usuario("abo", "abogado")
        self.secretaria = crear_usuario("sec", "secretario_juridico")
        self.exp = crear_expediente(self.abogado)

    def test_solo_el_administrador_ve_la_auditoria(self):
        for usuario in (self.abogado, self.secretaria):
            self.client.force_authenticate(usuario)
            self.assertEqual(self.client.get("/api/auditoria/").status_code, 403, usuario.username)
        self.client.force_authenticate(self.admin)
        r = self.client.get("/api/auditoria/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("actividad", r.data)
        self.assertIn("accesos", r.data)

    def test_registra_lo_que_hace_el_personal(self):
        self.client.force_authenticate(self.abogado)
        r = self.client.post(
            "/api/tareas/", {"titulo": "Radicar", "asignado_a": self.secretaria.pk, "expediente": self.exp.pk}, format="json"
        )
        self.assertEqual(r.status_code, 201, r.data)
        self.client.force_authenticate(self.admin)
        acciones = [a["accion"] for a in self.client.get("/api/auditoria/").data["actividad"]]
        self.assertIn("Tarea asignada", acciones)

    def test_filtra_por_usuario(self):
        self.client.force_authenticate(self.abogado)
        self.client.post(
            "/api/tareas/", {"titulo": "Radicar", "asignado_a": self.secretaria.pk, "expediente": self.exp.pk}, format="json"
        )
        self.client.force_authenticate(self.admin)
        propios = self.client.get(f"/api/auditoria/?usuario={self.abogado.pk}").data["actividad"]
        self.assertTrue(propios and all(a["usuario"] == "Abo Prueba" for a in propios))
        self.assertEqual(self.client.get(f"/api/auditoria/?usuario={self.secretaria.pk}").data["actividad"], [])
