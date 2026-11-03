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


class VacanciaJudicialTests(SimpleTestCase):
    def test_semana_santa_2026_es_de_lunes_a_viernes(self):
        from core.plazos import semana_santa

        self.assertEqual(semana_santa(2026), (date(2026, 3, 30), date(2026, 4, 3)))

    def test_fechas_de_vacancia_de_fin_de_ano(self):
        from core.plazos import es_vacancia_judicial

        self.assertFalse(es_vacancia_judicial(date(2026, 12, 19)))
        self.assertTrue(es_vacancia_judicial(date(2026, 12, 20)))
        self.assertTrue(es_vacancia_judicial(date(2027, 1, 10)))
        self.assertFalse(es_vacancia_judicial(date(2027, 1, 11)))

    def test_sin_vacancia_el_calculo_no_cambia(self):
        self.assertEqual(sumar_dias_habiles(date(2026, 12, 18), 1, vacancia=False), date(2026, 12, 21))

    def test_con_vacancia_salta_fin_de_ano(self):
        # 11 de enero de 2027 es festivo (Reyes Magos trasladado), por eso vence el martes 12
        self.assertEqual(sumar_dias_habiles(date(2026, 12, 18), 1, vacancia=True), date(2027, 1, 12))

    def test_con_vacancia_salta_semana_santa(self):
        self.assertEqual(sumar_dias_habiles(date(2026, 3, 27), 1, vacancia=True), date(2026, 4, 6))
        self.assertEqual(sumar_dias_habiles(date(2026, 3, 27), 1, vacancia=False), date(2026, 3, 30))

    def test_termino_que_no_toca_vacancia_es_igual_con_o_sin_ella(self):
        self.assertEqual(
            sumar_dias_habiles(date(2026, 8, 3), 20, vacancia=True), sumar_dias_habiles(date(2026, 8, 3), 20, vacancia=False)
        )

    def test_la_configuracion_del_sistema_se_usa_por_defecto(self):
        from django.test import override_settings

        with override_settings(PLAZOS_CON_VACANCIA=True):
            self.assertEqual(sumar_dias_habiles(date(2026, 12, 18), 1), date(2027, 1, 12))
        with override_settings(PLAZOS_CON_VACANCIA=False):
            self.assertEqual(sumar_dias_habiles(date(2026, 12, 18), 1), date(2026, 12, 21))

    def test_dias_de_vacancia_descontados(self):
        from core.plazos import dias_de_vacancia_en_rango

        self.assertEqual(dias_de_vacancia_en_rango(date(2026, 12, 18), date(2027, 1, 12)), 13)


class CalcularPlazoVacanciaApiTests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(crear_usuario("abog1", "abogado"))

    def test_parametro_vacancia(self):
        r = self.client.get("/api/plazos/calcular/", {"dias": 1, "fecha_inicio": "2026-12-18", "vacancia": "true"})
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["fecha_vencimiento"], "2027-01-12")
        self.assertTrue(r.data["con_vacancia_judicial"])
        self.assertEqual(r.data["dias_de_vacancia_descontados"], 13)
        self.assertIn("vacancia judicial", r.data["advertencia"])

    def test_sin_el_parametro_se_ignora_la_vacancia(self):
        r = self.client.get("/api/plazos/calcular/", {"dias": 1, "fecha_inicio": "2026-12-18"})
        self.assertEqual(r.data["fecha_vencimiento"], "2026-12-21")
        self.assertFalse(r.data["con_vacancia_judicial"])

    def test_valor_invalido(self):
        r = self.client.get("/api/plazos/calcular/", {"dias": 1, "vacancia": "tal vez"})
        self.assertEqual(r.status_code, 400)
