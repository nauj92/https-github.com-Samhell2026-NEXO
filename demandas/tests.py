from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase

from core.plazos import sumar_dias_habiles
from core.testutils import crear_cliente, crear_expediente, crear_usuario
from demandas.models import Citacion, ContestacionDemanda, Demanda
from notificaciones.models import Notificacion
from notificaciones.servicios import generar_para_usuario


class DemandaApiTests(APITestCase):
    def setUp(self):
        self.admin = crear_usuario("admin1", "administrador")
        self.abogado = crear_usuario("abog1", "abogado")
        self.otro = crear_usuario("abog2", "abogado")
        self.hoy = timezone.localdate()

    def datos(self, **extra):
        d = {
            "clase_proceso": "Ejecutivo singular",
            "demandante": "Inversiones Andina S.A.S.",
            "demandado": "Constructora Horizonte Ltda.",
            "pretensiones": "Pago de la obligación contenida en el pagaré y sus intereses de mora.",
            "cuantia": "25000000",
        }
        d.update(extra)
        return d

    def crear(self, **extra):
        return self.client.post("/api/demandas/", self.datos(**extra), format="json")

    def test_crea_demanda_en_elaboracion_a_cargo_de_quien_la_registra(self):
        self.client.force_authenticate(self.abogado)
        r = self.crear(cliente=crear_cliente().pk)
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["estado"], "elaboracion")
        self.assertEqual(r.data["abogado_responsable"], self.abogado.pk)
        self.assertIsNone(r.data["fecha_limite_subsanacion"])

    def test_validaciones_basicas(self):
        self.client.force_authenticate(self.abogado)
        self.assertEqual(self.crear(pretensiones="corta").status_code, 400)
        self.assertEqual(self.crear(cuantia="-1").status_code, 400)
        self.assertEqual(self.crear(demandante="  ").status_code, 400)
        self.assertEqual(self.crear(clase_proceso="x").status_code, 400)

    def test_radicada_exige_fecha_de_radicacion_no_futura(self):
        self.client.force_authenticate(self.abogado)
        r = self.crear(estado="radicada")
        self.assertEqual(r.status_code, 400)
        self.assertIn("fecha_radicacion", r.data)
        manana = (self.hoy + timedelta(days=1)).isoformat()
        self.assertEqual(self.crear(estado="radicada", fecha_radicacion=manana).status_code, 400)
        r = self.crear(estado="radicada", fecha_radicacion=self.hoy.isoformat())
        self.assertEqual(r.status_code, 201, r.data)

    def test_inadmitida_calcula_cinco_dias_habiles_para_subsanar(self):
        self.client.force_authenticate(self.abogado)
        radicacion = self.hoy - timedelta(days=20)
        inadmision = self.hoy - timedelta(days=5)
        r = self.crear(
            estado="inadmitida", fecha_radicacion=radicacion.isoformat(), fecha_inadmision=inadmision.isoformat()
        )
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["fecha_limite_subsanacion"], sumar_dias_habiles(inadmision, 5))

    def test_inadmitida_exige_fecha_de_inadmision_posterior_a_la_radicacion(self):
        self.client.force_authenticate(self.abogado)
        rad = (self.hoy - timedelta(days=10)).isoformat()
        self.assertEqual(self.crear(estado="inadmitida", fecha_radicacion=rad).status_code, 400)
        anterior = (self.hoy - timedelta(days=15)).isoformat()
        self.assertEqual(self.crear(estado="inadmitida", fecha_radicacion=rad, fecha_inadmision=anterior).status_code, 400)

    def test_admitida_exige_fecha_de_admision(self):
        self.client.force_authenticate(self.abogado)
        rad = (self.hoy - timedelta(days=10)).isoformat()
        r = self.crear(estado="admitida", fecha_radicacion=rad)
        self.assertEqual(r.status_code, 400)
        self.assertIn("fecha_admision", r.data)
        r = self.crear(estado="admitida", fecha_radicacion=rad, fecha_admision=self.hoy.isoformat())
        self.assertEqual(r.status_code, 201, r.data)

    def test_cambio_de_estado_por_patch_valida_con_lo_ya_guardado(self):
        self.client.force_authenticate(self.abogado)
        pk = self.crear().data["id"]
        r = self.client.patch(f"/api/demandas/{pk}/", {"estado": "radicada"}, format="json")
        self.assertEqual(r.status_code, 400)
        r = self.client.patch(f"/api/demandas/{pk}/", {"estado": "radicada", "fecha_radicacion": self.hoy.isoformat()}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["estado_display"], "Radicada")

    def test_cada_abogado_solo_ve_las_suyas_y_el_directivo_todas(self):
        self.client.force_authenticate(self.abogado)
        pk = self.crear().data["id"]
        self.client.force_authenticate(self.otro)
        self.assertEqual(len(self.client.get("/api/demandas/").data), 0)
        self.assertEqual(self.client.get(f"/api/demandas/{pk}/").status_code, 404)
        self.client.force_authenticate(self.admin)
        self.assertEqual(len(self.client.get("/api/demandas/").data), 1)

    def test_abogado_no_asigna_a_otro_pero_el_directivo_si(self):
        self.client.force_authenticate(self.abogado)
        r = self.crear(abogado_responsable=self.otro.pk)
        self.assertEqual(r.status_code, 400)
        self.assertIn("abogado_responsable", r.data)
        self.client.force_authenticate(self.admin)
        r = self.crear(abogado_responsable=self.otro.pk)
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["abogado_responsable"], self.otro.pk)

    def test_no_vincula_expediente_ajeno(self):
        ajeno = crear_expediente(self.otro)
        self.client.force_authenticate(self.abogado)
        self.assertEqual(self.crear(expediente=ajeno.pk).status_code, 400)
        propio = crear_expediente(self.abogado)
        r = self.crear(expediente=propio.pk)
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["expediente_numero"], propio.numero)

    def test_eliminar(self):
        self.client.force_authenticate(self.abogado)
        pk = self.crear().data["id"]
        self.assertEqual(self.client.delete(f"/api/demandas/{pk}/").status_code, 204)

    def test_notificacion_de_plazo_de_subsanacion_vencido(self):
        Demanda.objects.create(
            clase_proceso="Ordinario laboral", demandante="Ana Pérez", demandado="Empresa XYZ S.A.S.",
            pretensiones="Reconocimiento y pago de prestaciones sociales adeudadas.",
            estado="inadmitida", fecha_radicacion=self.hoy - timedelta(days=40),
            fecha_inadmision=self.hoy - timedelta(days=30), abogado_responsable=self.abogado,
        )
        self.assertGreaterEqual(generar_para_usuario(self.abogado), 1)
        nota = Notificacion.objects.get(usuario=self.abogado, clave__startswith="subsanacion:")
        self.assertIn("VENCIDO", nota.mensaje)
        generar_para_usuario(self.abogado)
        self.assertEqual(Notificacion.objects.filter(usuario=self.abogado, clave__startswith="subsanacion:").count(), 1)


class BorradorDemandaTests(APITestCase):
    def setUp(self):
        self.abogado = crear_usuario("abog1", "abogado")
        self.otro = crear_usuario("abog2", "abogado")
        self.client.force_authenticate(self.abogado)

    def test_genera_borrador_con_los_datos_de_la_demanda_sin_guardarlo(self):
        r = self.client.post(
            "/api/demandas/",
            {
                "clase_proceso": "Ejecutivo singular", "demandante": "Inversiones Andina S.A.S.",
                "demandado": "Constructora Horizonte Ltda.", "cuantia": "25000000",
                "pretensiones": "Se libre mandamiento de pago por el capital y los intereses de mora.",
            },
            format="json",
        )
        pk = r.data["id"]
        g = self.client.get(f"/api/demandas/{pk}/generar-borrador/")
        self.assertEqual(g.status_code, 200)
        texto = g.data["borrador"]
        self.assertIn("EJECUTIVO SINGULAR", texto)
        self.assertIn("Inversiones Andina S.A.S.", texto)
        self.assertIn("$25.000.000", texto)
        self.assertIn("Se libre mandamiento de pago", texto)
        self.assertEqual(self.client.get(f"/api/demandas/{pk}/").data["borrador"], "")
        # El abogado edita y guarda su versión
        r = self.client.patch(f"/api/demandas/{pk}/", {"borrador": "Texto final"}, format="json")
        self.assertEqual(r.data["borrador"], "Texto final")

    def test_no_genera_borrador_de_demanda_ajena(self):
        d = Demanda.objects.create(
            clase_proceso="Ordinario", demandante="Ana Pérez", demandado="Empresa XYZ", pretensiones="Pago de prestaciones sociales adeudadas.",
            abogado_responsable=self.otro,
        )
        self.assertEqual(self.client.get(f"/api/demandas/{d.pk}/generar-borrador/").status_code, 404)


class ContestacionApiTests(APITestCase):
    def setUp(self):
        self.admin = crear_usuario("admin1", "administrador")
        self.abogado = crear_usuario("abog1", "abogado")
        self.otro = crear_usuario("abog2", "abogado")
        self.hoy = timezone.localdate()

    def datos(self, **extra):
        d = {"clase_proceso": "Verbal", "demandante": "Ana Pérez", "demandado": "Distribuciones Norte S.A.S."}
        d.update(extra)
        return d

    def crear(self, **extra):
        return self.client.post("/api/contestaciones/", self.datos(**extra), format="json")

    def test_calcula_el_limite_con_dias_habiles(self):
        self.client.force_authenticate(self.abogado)
        notif = self.hoy - timedelta(days=3)
        r = self.crear(fecha_notificacion=notif.isoformat())
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["dias_termino"], 20)
        self.assertEqual(r.data["fecha_limite"], sumar_dias_habiles(notif, 20))
        self.assertEqual(r.data["abogado_responsable"], self.abogado.pk)
        self.assertEqual(r.data["estado"], "por_elaborar")

    def test_termino_distinto_por_clase_de_proceso(self):
        self.client.force_authenticate(self.abogado)
        notif = self.hoy - timedelta(days=1)
        r = self.crear(fecha_notificacion=notif.isoformat(), dias_termino=10)
        self.assertEqual(r.data["fecha_limite"], sumar_dias_habiles(notif, 10))
        self.assertEqual(self.crear(dias_termino=0).status_code, 400)
        self.assertEqual(self.crear(dias_termino=91).status_code, 400)

    def test_validaciones(self):
        self.client.force_authenticate(self.abogado)
        manana = (self.hoy + timedelta(days=1)).isoformat()
        self.assertEqual(self.crear(fecha_notificacion=manana).status_code, 400)
        r = self.crear(estado="presentada", fecha_notificacion=(self.hoy - timedelta(days=5)).isoformat())
        self.assertEqual(r.status_code, 400)
        self.assertIn("fecha_presentacion", r.data)
        r = self.crear(estado="presentada", fecha_notificacion=(self.hoy - timedelta(days=5)).isoformat(),
                       fecha_presentacion=(self.hoy - timedelta(days=6)).isoformat())
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.crear(demandado=" ").status_code, 400)

    def test_marca_extemporanea_si_se_presento_despues_del_limite(self):
        self.client.force_authenticate(self.abogado)
        notif = self.hoy - timedelta(days=60)
        r = self.crear(estado="presentada", fecha_notificacion=notif.isoformat(), fecha_presentacion=self.hoy.isoformat())
        self.assertEqual(r.status_code, 201, r.data)
        self.assertTrue(r.data["extemporanea"])
        self.assertIsNone(r.data["dias_restantes"])

    def test_borrador_de_contestacion(self):
        self.client.force_authenticate(self.abogado)
        pk = self.crear(excepciones="Prescripción de la acción cambiaria.").data["id"]
        texto = self.client.get(f"/api/contestaciones/{pk}/generar-borrador/").data["borrador"]
        self.assertIn("CONTESTACIÓN DE LA DEMANDA", texto)
        self.assertIn("Prescripción de la acción cambiaria.", texto)

    def test_alcance_por_abogado(self):
        self.client.force_authenticate(self.abogado)
        pk = self.crear().data["id"]
        self.client.force_authenticate(self.otro)
        self.assertEqual(len(self.client.get("/api/contestaciones/").data), 0)
        self.assertEqual(self.client.get(f"/api/contestaciones/{pk}/").status_code, 404)
        self.client.force_authenticate(self.admin)
        self.assertEqual(len(self.client.get("/api/contestaciones/").data), 1)

    def test_notificacion_de_termino_vencido(self):
        ContestacionDemanda.objects.create(
            clase_proceso="Verbal", demandante="Ana Pérez", demandado="Distribuciones Norte S.A.S.",
            fecha_notificacion=self.hoy - timedelta(days=60), abogado_responsable=self.abogado,
        )
        generar_para_usuario(self.abogado)
        nota = Notificacion.objects.get(usuario=self.abogado, clave__startswith="contestacion:")
        self.assertIn("VENCIDO", nota.mensaje)
        generar_para_usuario(self.abogado)
        self.assertEqual(Notificacion.objects.filter(usuario=self.abogado, clave__startswith="contestacion:").count(), 1)

    def test_presentada_ya_no_notifica(self):
        ContestacionDemanda.objects.create(
            clase_proceso="Verbal", demandante="Ana Pérez", demandado="X S.A.S.", estado="presentada",
            fecha_notificacion=self.hoy - timedelta(days=60), fecha_presentacion=self.hoy - timedelta(days=50),
            abogado_responsable=self.abogado,
        )
        generar_para_usuario(self.abogado)
        self.assertFalse(Notificacion.objects.filter(usuario=self.abogado, clave__startswith="contestacion:").exists())


class CitacionApiTests(APITestCase):
    def setUp(self):
        self.admin = crear_usuario("admin1", "administrador")
        self.abogado = crear_usuario("abog1", "abogado")
        self.otro = crear_usuario("abog2", "abogado")
        self.hoy = timezone.localdate()

    def crear(self, **extra):
        d = {"destinatario": "Julián Esteban Ramos", "direccion": "Calle 10 # 5-20, Cali"}
        d.update(extra)
        return self.client.post("/api/citaciones/", d, format="json")

    def test_crea_citacion_pendiente(self):
        self.client.force_authenticate(self.abogado)
        r = self.crear()
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["estado"], "pendiente")
        self.assertEqual(r.data["tipo"], "citacion")
        self.assertIsNone(r.data["fecha_limite_comparecencia"])

    def test_plazo_de_comparecencia_segun_ubicacion(self):
        self.client.force_authenticate(self.abogado)
        envio = self.hoy - timedelta(days=4)
        entrega = self.hoy - timedelta(days=2)
        for ubicacion, dias in [("mismo_municipio", 5), ("otro_municipio", 10), ("exterior", 30)]:
            r = self.crear(estado="entregada", ubicacion=ubicacion, fecha_envio=envio.isoformat(), fecha_entrega=entrega.isoformat())
            self.assertEqual(r.status_code, 201, r.data)
            self.assertEqual(r.data["fecha_limite_comparecencia"], sumar_dias_habiles(entrega, dias))

    def test_aviso_calcula_cuando_surte_efecto(self):
        self.client.force_authenticate(self.abogado)
        entrega = self.hoy - timedelta(days=2)
        r = self.crear(tipo="aviso", estado="entregada", fecha_envio=(self.hoy - timedelta(days=4)).isoformat(), fecha_entrega=entrega.isoformat())
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["fecha_surte_efecto"], sumar_dias_habiles(entrega, 1))
        self.assertIsNone(r.data["fecha_limite_comparecencia"])

    def test_validaciones_de_fechas_y_estado(self):
        self.client.force_authenticate(self.abogado)
        self.assertEqual(self.crear(estado="enviada").status_code, 400)  # falta fecha de envío
        manana = (self.hoy + timedelta(days=1)).isoformat()
        self.assertEqual(self.crear(estado="enviada", fecha_envio=manana).status_code, 400)
        r = self.crear(estado="entregada", fecha_envio=self.hoy.isoformat())
        self.assertEqual(r.status_code, 400)
        self.assertIn("fecha_entrega", r.data)
        r = self.crear(estado="entregada", fecha_envio=self.hoy.isoformat(), fecha_entrega=(self.hoy - timedelta(days=1)).isoformat())
        self.assertEqual(r.status_code, 400)
        r = self.crear(estado="notificado", fecha_envio=self.hoy.isoformat())
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.crear(destinatario=" ").status_code, 400)

    def test_alcance_por_abogado(self):
        self.client.force_authenticate(self.abogado)
        self.crear()
        self.client.force_authenticate(self.otro)
        self.assertEqual(len(self.client.get("/api/citaciones/").data), 0)
        self.client.force_authenticate(self.admin)
        self.assertEqual(len(self.client.get("/api/citaciones/").data), 1)

    def test_notificacion_cuando_vence_el_plazo_de_comparecencia(self):
        Citacion.objects.create(
            destinatario="Julián Esteban Ramos", estado="entregada", fecha_envio=self.hoy - timedelta(days=40),
            fecha_entrega=self.hoy - timedelta(days=30), abogado_responsable=self.abogado,
        )
        generar_para_usuario(self.abogado)
        nota = Notificacion.objects.get(usuario=self.abogado, clave__startswith="citacion:")
        self.assertIn("aviso", nota.mensaje)
        generar_para_usuario(self.abogado)
        self.assertEqual(Notificacion.objects.filter(usuario=self.abogado, clave__startswith="citacion:").count(), 1)

    def test_notificado_ya_no_alerta(self):
        Citacion.objects.create(
            destinatario="Julián Esteban Ramos", estado="notificado", fecha_envio=self.hoy - timedelta(days=40),
            fecha_entrega=self.hoy - timedelta(days=30), fecha_notificacion=self.hoy - timedelta(days=28),
            abogado_responsable=self.abogado,
        )
        generar_para_usuario(self.abogado)
        self.assertFalse(Notificacion.objects.filter(usuario=self.abogado, clave__startswith="citacion:").exists())
