from datetime import date

from django.test import SimpleTestCase
from rest_framework.test import APITestCase

from core.plazos import es_dia_habil, festivos, sumar_dias_habiles
from core.testutils import crear_usuario


class FestivosTests(SimpleTestCase):
    def test_festivos_2026_coinciden_con_el_calendario_oficial(self):
        esperados = {
            date(2026, 1, 1), date(2026, 1, 12), date(2026, 3, 23), date(2026, 4, 2), date(2026, 4, 3),
            date(2026, 5, 1), date(2026, 5, 18), date(2026, 6, 8), date(2026, 6, 15), date(2026, 6, 29),
            date(2026, 7, 20), date(2026, 8, 7), date(2026, 8, 17), date(2026, 10, 12), date(2026, 11, 2),
            date(2026, 11, 16), date(2026, 12, 8), date(2026, 12, 25),
        }
        self.assertEqual(set(festivos(2026)), esperados)

    def test_ley_emiliani_traslada_al_lunes(self):
        # 19 de marzo de 2026 es jueves -> el festivo de San José pasa al lunes 23
        self.assertIn(date(2026, 3, 23), festivos(2026))
        self.assertNotIn(date(2026, 3, 19), festivos(2026))

    def test_dia_habil(self):
        self.assertTrue(es_dia_habil(date(2026, 10, 15)))   # jueves normal
        self.assertFalse(es_dia_habil(date(2026, 10, 17)))  # sábado
        self.assertFalse(es_dia_habil(date(2026, 10, 12)))  # festivo (lunes)


class SumarDiasHabilesTests(SimpleTestCase):
    def test_salta_fines_de_semana(self):
        # Viernes 16 de octubre de 2026 + 10 días hábiles = viernes 30 de octubre
        self.assertEqual(sumar_dias_habiles(date(2026, 10, 16), 10), date(2026, 10, 30))

    def test_salta_festivo(self):
        # Viernes 20 de marzo + 1 día hábil: el lunes 23 es festivo -> martes 24
        self.assertEqual(sumar_dias_habiles(date(2026, 3, 20), 1), date(2026, 3, 24))

    def test_semana_santa(self):
        # Miércoles 1 de abril + 1: jueves y viernes santos, fin de semana -> lunes 6
        self.assertEqual(sumar_dias_habiles(date(2026, 4, 1), 1), date(2026, 4, 6))

    def test_cero_dias_devuelve_la_misma_fecha(self):
        self.assertEqual(sumar_dias_habiles(date(2026, 10, 16), 0), date(2026, 10, 16))


class CalcularPlazoApiTests(APITestCase):
    url = "/api/plazos/calcular/"

    def test_requiere_autenticacion(self):
        self.assertEqual(self.client.get(self.url, {"dias": 10}).status_code, 401)

    def test_calcula_vencimiento(self):
        self.client.force_authenticate(crear_usuario("abogado1"))
        r = self.client.get(self.url, {"dias": 10, "fecha_inicio": "2026-10-16"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["fecha_vencimiento"], "2026-10-30")
        self.assertIn("advertencia", r.data)

    def test_incluye_los_festivos_del_rango(self):
        self.client.force_authenticate(crear_usuario("abogado1"))
        r = self.client.get(self.url, {"dias": 1, "fecha_inicio": "2026-03-20"})
        self.assertEqual([f["fecha"] for f in r.data["festivos_en_el_rango"]], ["2026-03-23"])

    def test_valida_parametros(self):
        self.client.force_authenticate(crear_usuario("abogado1"))
        self.assertEqual(self.client.get(self.url, {"dias": "abc"}).status_code, 400)
        self.assertEqual(self.client.get(self.url, {"dias": 0}).status_code, 400)
        self.assertEqual(self.client.get(self.url, {"dias": 5, "fecha_inicio": "16/10/2026"}).status_code, 400)
