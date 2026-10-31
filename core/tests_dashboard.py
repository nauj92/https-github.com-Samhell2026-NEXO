from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase

from audiencias.models import Audiencia
from core.plazos import sumar_dias_habiles
from core.testutils import crear_cliente, crear_expediente, crear_usuario
from demandas.models import ContestacionDemanda, Demanda
from expedientes.models import EtapaProceso

URL = "/api/dashboard/resumen/"


class DashboardResumenTests(APITestCase):
    def setUp(self):
        self.admin = crear_usuario("admin1", "administrador")
        self.abogado = crear_usuario("abog1", "abogado")
        self.otro = crear_usuario("abog2", "abogado")
        self.hoy = timezone.localdate()
        self.exp = crear_expediente(self.abogado)
        self.exp_ajeno = crear_expediente(self.otro)

    def test_exige_autenticacion(self):
        self.assertEqual(self.client.get(URL).status_code, 401)

    def test_expedientes_segun_rol(self):
        self.client.force_authenticate(self.abogado)
        self.assertEqual(self.client.get(URL).data["expedientes"]["activos"], 1)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get(URL).data["expedientes"]["activos"], 2)

    def test_abogados_total_solo_para_directivos(self):
        self.client.force_authenticate(self.abogado)
        self.assertNotIn("abogados_total", self.client.get(URL).data)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get(URL).data["abogados_total"], 3)

    def test_audiencias_proximas_solo_visibles_y_dentro_de_30_dias(self):
        ahora = timezone.now()
        Audiencia.objects.create(expediente=self.exp, fecha_hora=ahora + timedelta(days=2), lugar="Sala 1")
        Audiencia.objects.create(expediente=self.exp, fecha_hora=ahora + timedelta(days=90), lugar="Sala 2")
        Audiencia.objects.create(expediente=self.exp_ajeno, fecha_hora=ahora + timedelta(days=2), lugar="Sala 3")
        self.client.force_authenticate(self.abogado)
        datos = self.client.get(URL).data
        self.assertEqual([a["lugar"] for a in datos["audiencias_proximas"]], ["Sala 1"])

    def test_plazos_incluyen_vencidos_y_proximos(self):
        EtapaProceso.objects.create(expediente=self.exp, nombre="Vencida", fecha_limite=self.hoy - timedelta(days=1))
        EtapaProceso.objects.create(expediente=self.exp, nombre="Lejana", fecha_limite=self.hoy + timedelta(days=60))
        EtapaProceso.objects.create(expediente=self.exp, nombre="Hecha", fecha_limite=self.hoy - timedelta(days=3), estado="completada")
        self.client.force_authenticate(self.abogado)
        datos = self.client.get(URL).data
        self.assertEqual([p["titulo"] for p in datos["plazos"]], ["Vencida"])
        self.assertEqual(datos["plazos_vencidos"], 1)

    def test_demandas_por_estado_y_alcance(self):
        base = {"clase_proceso": "Ejecutivo", "demandante": "A", "demandado": "B", "pretensiones": "x"}
        Demanda.objects.create(abogado_responsable=self.abogado, **base)
        Demanda.objects.create(abogado_responsable=self.otro, estado="radicada", **base)
        self.client.force_authenticate(self.abogado)
        datos = self.client.get(URL).data
        self.assertEqual(datos["demandas_total"], 1)
        self.assertEqual(datos["demandas_por_estado"], {"elaboracion": 1})
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get(URL).data["demandas_total"], 2)

    def test_contestaciones_pendientes_con_fecha_limite(self):
        notif = self.hoy - timedelta(days=40)
        base = {"clase_proceso": "Ejecutivo", "demandante": "A", "demandado": "Cliente", "abogado_responsable": self.abogado}
        ContestacionDemanda.objects.create(fecha_notificacion=notif, **base)
        ContestacionDemanda.objects.create(fecha_notificacion=notif, estado="presentada", **base)
        ContestacionDemanda.objects.create(**base)  # sin fecha de notificación: no se puede calcular
        self.client.force_authenticate(self.abogado)
        datos = self.client.get(URL).data
        self.assertEqual(datos["contestaciones_pendientes_total"], 1)
        item = datos["contestaciones_pendientes"][0]
        self.assertEqual(item["fecha_limite"], sumar_dias_habiles(notif, 20).isoformat())
        self.assertEqual(datos["contestaciones_vencidas"], 1)

    def test_clientes_total(self):
        crear_cliente("Uno")
        crear_cliente("Dos")
        self.client.force_authenticate(self.abogado)
        self.assertEqual(self.client.get(URL).data["clientes_total"], 2)

    def test_totales_y_casos_por_rama(self):
        ahora = timezone.now()
        Audiencia.objects.create(expediente=self.exp, tipo="audiencia", fecha_hora=ahora, lugar="A")
        Audiencia.objects.create(expediente=self.exp, tipo="diligencia", fecha_hora=ahora, lugar="B")
        crear_expediente(self.abogado, materia="Derecho de Familia")
        crear_expediente(self.abogado, materia="Penal")
        crear_expediente(self.abogado, materia="Contencioso administrativo")
        crear_expediente(self.abogado, materia="Laboral")
        self.client.force_authenticate(self.abogado)
        datos = self.client.get(URL).data
        ramas = {r["rama"]: r["total"] for r in datos["casos_por_rama"]}
        self.assertEqual(ramas, {"Civil": 1, "Familia": 1, "Penal": 1, "Administrativo": 1, "Laboral": 1})
        self.assertEqual(datos["totales"]["audiencias"], 1)
        self.assertEqual(datos["totales"]["diligencias"], 1)
        self.assertEqual(datos["totales"]["expedientes"], 5)
        self.assertNotIn("abogados", datos["totales"])
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get(URL).data["totales"]["abogados"], 3)

    def test_rama_usa_especialidad_del_despacho_si_la_materia_no_aclara(self):
        from core.dashboard import rama_de
        from expedientes.models import Juzgado

        j = Juzgado.objects.create(nombre="Juzgado X", especialidad="FAMILIA ORALIDAD")
        e = crear_expediente(self.abogado, materia="Asunto 123", juzgado=j)
        self.assertEqual(rama_de(e), "Familia")
