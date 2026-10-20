from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase

from core.testutils import crear_expediente, crear_usuario
from notificaciones.models import Notificacion
from notificaciones.servicios import generar_para_usuario
from vigilancia.models import Vigilancia


class VigilanciaApiTests(APITestCase):
    def setUp(self):
        self.admin = crear_usuario("admin1", "administrador")
        self.abogado = crear_usuario("abog1", "abogado")
        self.otro = crear_usuario("abog2", "abogado")
        self.exp = crear_expediente(self.abogado)
        self.exp_ajeno = crear_expediente(self.otro)

    def crear(self, exp=None, **extra):
        return self.client.post("/api/vigilancia/", {"expediente": (exp or self.exp).pk, **extra}, format="json")

    def test_crea_vigilancia_de_un_expediente_propio(self):
        self.client.force_authenticate(self.abogado)
        r = self.crear(dias_alerta=15)
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["expediente_numero"], self.exp.numero)
        self.assertEqual(r.data["dias_alerta"], 15)
        self.assertFalse(r.data["alerta"])
        self.assertEqual(r.data["total_actuaciones"], 0)

    def test_no_repite_ni_acepta_cerrados_ni_ajenos(self):
        self.client.force_authenticate(self.abogado)
        self.crear()
        r = self.crear()
        self.assertEqual(r.status_code, 400)
        self.assertIn("ya está en vigilancia", str(r.data["expediente"][0]))
        cerrado = crear_expediente(self.abogado, estado="cerrado")
        self.assertEqual(self.crear(cerrado).status_code, 400)
        self.assertEqual(self.crear(self.exp_ajeno).status_code, 400)
        self.assertEqual(self.crear(dias_alerta=0).status_code, 400)

    def test_cada_abogado_solo_ve_las_suyas(self):
        self.client.force_authenticate(self.abogado)
        self.crear()
        self.client.force_authenticate(self.otro)
        self.assertEqual(len(self.client.get("/api/vigilancia/").data), 0)
        self.client.force_authenticate(self.admin)
        self.assertEqual(len(self.client.get("/api/vigilancia/").data), 1)

    def test_registrar_y_eliminar_actuaciones(self):
        self.client.force_authenticate(self.abogado)
        pk = self.crear().data["id"]
        hoy = timezone.localdate()
        r = self.client.post(f"/api/vigilancia/{pk}/actuaciones/", {"fecha": hoy.isoformat(), "descripcion": "Auto fija fecha de audiencia"}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(len(self.client.get(f"/api/vigilancia/{pk}/actuaciones/").data), 1)
        det = self.client.get(f"/api/vigilancia/{pk}/").data
        self.assertEqual(det["total_actuaciones"], 1)
        self.assertEqual(det["ultima_descripcion"], "Auto fija fecha de audiencia")
        act_id = r.data["id"]
        self.assertEqual(self.client.delete(f"/api/vigilancia/{pk}/actuaciones/{act_id}/").status_code, 204)
        self.assertEqual(self.client.delete(f"/api/vigilancia/{pk}/actuaciones/{act_id}/").status_code, 404)

    def test_rechaza_actuacion_futura_o_sin_descripcion(self):
        self.client.force_authenticate(self.abogado)
        pk = self.crear().data["id"]
        manana = (timezone.localdate() + timedelta(days=1)).isoformat()
        r = self.client.post(f"/api/vigilancia/{pk}/actuaciones/", {"fecha": manana, "descripcion": "Auto de prueba"}, format="json")
        self.assertEqual(r.status_code, 400)
        r = self.client.post(f"/api/vigilancia/{pk}/actuaciones/", {"fecha": timezone.localdate().isoformat(), "descripcion": "ok"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_alerta_por_falta_de_movimiento_y_se_limpia_al_registrar(self):
        self.client.force_authenticate(self.abogado)
        pk = self.crear(dias_alerta=30).data["id"]
        Vigilancia.objects.filter(pk=pk).update(creado_en=timezone.now() - timedelta(days=40))
        det = self.client.get(f"/api/vigilancia/{pk}/").data
        self.assertTrue(det["alerta"])
        self.assertEqual(det["dias_sin_movimiento"], 40)
        self.client.post(f"/api/vigilancia/{pk}/actuaciones/", {"fecha": timezone.localdate().isoformat(), "descripcion": "Memorial radicado"}, format="json")
        det = self.client.get(f"/api/vigilancia/{pk}/").data
        self.assertFalse(det["alerta"])
        self.assertEqual(det["dias_sin_movimiento"], 0)

    def test_vigilancia_inactiva_no_alerta(self):
        self.client.force_authenticate(self.abogado)
        pk = self.crear(dias_alerta=5).data["id"]
        Vigilancia.objects.filter(pk=pk).update(creado_en=timezone.now() - timedelta(days=40))
        self.client.patch(f"/api/vigilancia/{pk}/", {"activa": False}, format="json")
        self.assertFalse(self.client.get(f"/api/vigilancia/{pk}/").data["alerta"])

    def test_notificacion_automatica_sin_duplicados(self):
        self.client.force_authenticate(self.abogado)
        pk = self.crear(dias_alerta=30).data["id"]
        Vigilancia.objects.filter(pk=pk).update(creado_en=timezone.now() - timedelta(days=45))
        self.assertGreaterEqual(generar_para_usuario(self.abogado), 1)
        notas = Notificacion.objects.filter(usuario=self.abogado, mensaje__startswith="Vigilancia")
        self.assertEqual(notas.count(), 1)
        self.assertIn(self.exp.numero, notas.first().mensaje)
        generar_para_usuario(self.abogado)
        self.assertEqual(notas.count(), 1)

    def test_ancla_y_elimina_enlaces(self):
        self.client.force_authenticate(self.abogado)
        pk = self.crear().data["id"]
        r = self.client.post(
            f"/api/vigilancia/{pk}/enlaces/",
            {"titulo": "Consulta Rama Judicial", "url": "https://consultaprocesos.ramajudicial.gov.co/", "nota": "Buscar por radicado"},
            format="json",
        )
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(len(self.client.get(f"/api/vigilancia/{pk}/enlaces/").data), 1)
        self.assertEqual(self.client.get(f"/api/vigilancia/{pk}/").data["total_enlaces"], 1)
        eid = r.data["id"]
        self.assertEqual(self.client.delete(f"/api/vigilancia/{pk}/enlace/{eid}/").status_code, 204)
        self.assertEqual(self.client.delete(f"/api/vigilancia/{pk}/enlace/{eid}/").status_code, 404)

    def test_rechaza_enlaces_peligrosos_o_invalidos(self):
        self.client.force_authenticate(self.abogado)
        pk = self.crear().data["id"]
        for url in ["javascript:alert(1)", "ftp://servidor/archivo", "no es un enlace", "data:text/html,hola"]:
            r = self.client.post(f"/api/vigilancia/{pk}/enlaces/", {"titulo": "Prueba", "url": url}, format="json")
            self.assertEqual(r.status_code, 400, url)
        r = self.client.post(f"/api/vigilancia/{pk}/enlaces/", {"titulo": "x", "url": "https://ejemplo.com"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_no_se_ancla_a_proceso_ajeno(self):
        self.client.force_authenticate(self.abogado)
        pk = self.crear().data["id"]
        self.client.force_authenticate(self.otro)
        r = self.client.post(f"/api/vigilancia/{pk}/enlaces/", {"titulo": "Prueba", "url": "https://ejemplo.com"}, format="json")
        self.assertEqual(r.status_code, 404)
