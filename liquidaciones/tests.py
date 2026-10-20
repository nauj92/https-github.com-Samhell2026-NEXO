from rest_framework.test import APITestCase

from core.testutils import crear_expediente, crear_usuario
from liquidaciones.models import Liquidacion

LABORAL = {
    "salario_mensual": "2000000",
    "auxilio_transporte": "200000",
    "fecha_inicio": "2023-03-01",
    "fecha_fin": "2026-10-15",
    "indemnizacion": True,
    "salario_minimo": "1750905",
}
CREDITO = {"capital": "10000000", "fecha_inicio_mora": "2026-01-01", "fecha_corte": "2026-06-30", "tasa_ea": "30"}
CUOTAS = {
    "valor_cuota": "300000", "mes_inicial": "2026-01-01", "mes_final": "2026-06-01",
    "dia_vencimiento": 5, "fecha_corte": "2026-06-30", "tasa_ea": "30",
}
ALIMENTOS = {
    "valor_cuota": "500000", "mes_inicial": "2026-01-01", "mes_final": "2026-06-01",
    "dia_vencimiento": 5, "fecha_corte": "2026-06-30", "incremento_anual": "5", "tasa_ea": "6",
}


class LiquidacionApiTests(APITestCase):
    def setUp(self):
        self.admin = crear_usuario("admin1", "administrador")
        self.abogado = crear_usuario("abog1", "abogado")
        self.otro = crear_usuario("abog2", "abogado")

    def calcular(self, tipo, datos):
        return self.client.post("/api/liquidaciones/calcular/", {"tipo": tipo, "datos": datos}, format="json")

    def test_requiere_autenticacion(self):
        self.assertEqual(self.calcular("laboral", LABORAL).status_code, 401)

    def test_calcula_los_tres_tipos_sin_guardar(self):
        self.client.force_authenticate(self.abogado)
        r = self.calcular("laboral", LABORAL)
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["resultado"]["total"], 11_673_792)
        r = self.calcular("credito", CREDITO)
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["resultado"]["capital_inicial"], 10_000_000)
        r = self.calcular("cuotas", CUOTAS)
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["resultado"]["total"], 1_933_731)
        self.assertEqual(Liquidacion.objects.count(), 0)

    def test_calcula_y_guarda_alimentos(self):
        self.client.force_authenticate(self.abogado)
        r = self.calcular("alimentos", ALIMENTOS)
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["resultado"]["capital"], 3_000_000)
        r = self.client.post("/api/liquidaciones/", {"tipo": "alimentos", "referencia": "Alimentos Gómez", "datos": ALIMENTOS}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["tipo_display"], "Alimentos")

    def test_datos_invalidos_dan_mensaje_claro(self):
        self.client.force_authenticate(self.abogado)
        r = self.calcular("laboral", {**LABORAL, "fecha_fin": "2020-01-01"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("datos", r.data)
        r = self.calcular("credito", {**CREDITO, "capital": "-5"})
        self.assertEqual(r.status_code, 400)
        r = self.calcular("credito", {k: v for k, v in CREDITO.items() if k != "tasa_ea"})
        self.assertEqual(r.status_code, 400)
        r = self.calcular("otro", {})
        self.assertEqual(r.status_code, 400)

    def test_guardar_requiere_referencia_y_calcula_en_el_servidor(self):
        self.client.force_authenticate(self.abogado)
        r = self.client.post("/api/liquidaciones/", {"tipo": "credito", "datos": CREDITO}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("referencia", r.data)
        # El total que envíe el cliente se ignora: lo calcula el servidor
        r = self.client.post(
            "/api/liquidaciones/", {"tipo": "credito", "referencia": "Pagaré Pérez", "datos": CREDITO, "total": 1}, format="json"
        )
        self.assertEqual(r.status_code, 201, r.data)
        self.assertGreater(float(r.data["total"]), 10_000_000)
        self.assertEqual(r.data["creado_por_nombre"], "Abog1 Prueba")

    def test_cada_abogado_solo_ve_las_suyas_y_el_directivo_todas(self):
        self.client.force_authenticate(self.abogado)
        self.client.post("/api/liquidaciones/", {"tipo": "cuotas", "referencia": "Conjunto A", "datos": CUOTAS}, format="json")
        self.client.force_authenticate(self.otro)
        self.assertEqual(len(self.client.get("/api/liquidaciones/").data), 0)
        self.client.force_authenticate(self.admin)
        self.assertEqual(len(self.client.get("/api/liquidaciones/").data), 1)

    def test_no_se_puede_asociar_a_expediente_ajeno(self):
        ajeno = crear_expediente(self.otro)
        self.client.force_authenticate(self.abogado)
        r = self.client.post(
            "/api/liquidaciones/", {"tipo": "cuotas", "referencia": "X", "datos": CUOTAS, "expediente": ajeno.pk}, format="json"
        )
        self.assertEqual(r.status_code, 400)
        propio = crear_expediente(self.abogado)
        r = self.client.post(
            "/api/liquidaciones/", {"tipo": "cuotas", "referencia": "X", "datos": CUOTAS, "expediente": propio.pk}, format="json"
        )
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["expediente_numero"], propio.numero)

    def test_liquidacion_de_expediente_visible_la_ve_quien_lo_tiene_asignado(self):
        propio = crear_expediente(self.otro)
        self.client.force_authenticate(self.admin)
        self.client.post(
            "/api/liquidaciones/", {"tipo": "cuotas", "referencia": "X", "datos": CUOTAS, "expediente": propio.pk}, format="json"
        )
        self.client.force_authenticate(self.otro)
        self.assertEqual(len(self.client.get("/api/liquidaciones/").data), 1)

    def test_eliminar_solo_el_autor_o_directivo(self):
        self.client.force_authenticate(self.abogado)
        pk = self.client.post(
            "/api/liquidaciones/", {"tipo": "cuotas", "referencia": "X", "datos": CUOTAS}, format="json"
        ).data["id"]
        self.client.force_authenticate(self.otro)
        self.assertEqual(self.client.delete(f"/api/liquidaciones/{pk}/").status_code, 404)
        self.client.force_authenticate(self.abogado)
        self.assertEqual(self.client.delete(f"/api/liquidaciones/{pk}/").status_code, 204)

    def test_no_se_edita_una_liquidacion_guardada(self):
        self.client.force_authenticate(self.abogado)
        pk = self.client.post(
            "/api/liquidaciones/", {"tipo": "cuotas", "referencia": "X", "datos": CUOTAS}, format="json"
        ).data["id"]
        self.assertEqual(self.client.patch(f"/api/liquidaciones/{pk}/", {"referencia": "Y"}, format="json").status_code, 405)
