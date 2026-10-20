from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase

from audiencias.models import Audiencia
from core.testutils import crear_expediente, crear_usuario


class AudienciaApiTests(APITestCase):
    def setUp(self):
        self.admin = crear_usuario("admin1", "administrador")
        self.abogado = crear_usuario("abog1", "abogado")
        self.otro = crear_usuario("abog2", "abogado")
        self.exp = crear_expediente(self.abogado)
        self.exp2 = crear_expediente(self.abogado)
        self.exp_ajeno = crear_expediente(self.otro)
        self.manana = (timezone.now() + timedelta(days=1)).replace(microsecond=0)

    def crear(self, exp=None, fecha=None, lugar="Sala 4, Palacio de Justicia"):
        return self.client.post(
            "/api/audiencias/",
            {"expediente": (exp or self.exp).pk, "fecha_hora": (fecha or self.manana).isoformat(), "lugar": lugar},
            format="json",
        )

    def test_programa_audiencia_futura(self):
        self.client.force_authenticate(self.abogado)
        r = self.crear()
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["expediente_numero"], self.exp.numero)

    def test_tipo_por_defecto_es_audiencia_y_acepta_diligencia(self):
        self.client.force_authenticate(self.abogado)
        r = self.crear()
        self.assertEqual(r.data["tipo"], "audiencia")
        r = self.client.post(
            "/api/audiencias/",
            {"expediente": self.exp2.pk, "fecha_hora": (self.manana + timedelta(days=2)).isoformat(), "lugar": "Predio objeto del proceso",
             "tipo": "diligencia", "clase": "Inspección judicial"},
            format="json",
        )
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["tipo"], "diligencia")
        r = self.client.post(
            "/api/audiencias/",
            {"expediente": self.exp2.pk, "fecha_hora": (self.manana + timedelta(days=5)).isoformat(), "lugar": "Sala 2", "tipo": "otra"},
            format="json",
        )
        self.assertEqual(r.status_code, 400)

    def test_rechaza_fecha_en_el_pasado(self):
        self.client.force_authenticate(self.abogado)
        r = self.crear(fecha=timezone.now() - timedelta(days=1))
        self.assertEqual(r.status_code, 400)
        self.assertIn("pasado", str(r.data["fecha_hora"][0]))

    def test_rechaza_expediente_cerrado(self):
        cerrado = crear_expediente(self.abogado, estado="cerrado")
        self.client.force_authenticate(self.abogado)
        r = self.crear(exp=cerrado)
        self.assertEqual(r.status_code, 400)
        self.assertIn("expediente", r.data)

    def test_no_se_puede_programar_en_expediente_ajeno(self):
        self.client.force_authenticate(self.abogado)
        self.assertEqual(self.crear(exp=self.exp_ajeno).status_code, 400)
        self.assertEqual(Audiencia.objects.count(), 0)

    def test_el_abogado_no_puede_tener_dos_audiencias_a_la_misma_hora(self):
        self.client.force_authenticate(self.abogado)
        self.assertEqual(self.crear().status_code, 201)
        r = self.crear(exp=self.exp2, fecha=self.manana + timedelta(minutes=30))
        self.assertEqual(r.status_code, 400)
        self.assertIn("ya tiene otra audiencia", str(r.data["fecha_hora"][0]))

    def test_dos_horas_de_separacion_si_se_permite(self):
        self.client.force_authenticate(self.abogado)
        self.assertEqual(self.crear().status_code, 201)
        self.assertEqual(self.crear(exp=self.exp2, fecha=self.manana + timedelta(hours=2)).status_code, 201)

    def test_abogados_distintos_pueden_coincidir_en_hora(self):
        self.client.force_authenticate(self.abogado)
        self.assertEqual(self.crear().status_code, 201)
        self.client.force_authenticate(self.otro)
        self.assertEqual(self.crear(exp=self.exp_ajeno).status_code, 201)

    def test_editar_la_misma_audiencia_no_choca_consigo_misma(self):
        self.client.force_authenticate(self.abogado)
        aud = self.crear().data
        r = self.client.patch(f"/api/audiencias/{aud['id']}/", {"lugar": "Sala 9, Palacio de Justicia"}, format="json")
        self.assertEqual(r.status_code, 200, r.data)

    def test_cada_usuario_ve_solo_sus_audiencias(self):
        self.client.force_authenticate(self.abogado)
        self.crear()
        self.client.force_authenticate(self.otro)
        self.crear(exp=self.exp_ajeno)
        self.assertEqual(len(self.client.get("/api/audiencias/").data), 1)
        self.client.force_authenticate(self.admin)
        self.assertEqual(len(self.client.get("/api/audiencias/").data), 2)
