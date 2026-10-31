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


COMPLETA = {
    "clase_proceso": "Ejecutivo singular",
    "demandante": "Inversiones Andina S.A.S.",
    "demandado": "Constructora Horizonte Ltda.",
    "pretensiones": "Se libre mandamiento de pago por el capital y los intereses de mora.",
    "cuantia": "25000000",
    "juez_destinatario": "Juez Civil del Circuito de Cali (Reparto)",
    "demandante_tipo_persona": "juridica",
    "demandante_tipo_documento": "NIT",
    "demandante_documento": "900.123.456-7",
    "demandante_domicilio": "Cali, Valle del Cauca",
    "demandante_representante": "Luis Fernando Pérez",
    "demandado_tipo_persona": "juridica",
    "demandado_tipo_documento": "NIT",
    "demandado_documento": "800765432-1",
    "demandado_domicilio": "Bogotá D.C.",
    "demandado_representante": "Marta Gómez",
    "apoderado_nombre": "Camila Herrera Gonzales",
    "apoderado_documento": "31.000.000",
    "apoderado_tarjeta_profesional": "123456",
    "hechos": ["El 1 de marzo de 2025 las partes suscribieron el contrato.", "El demandado incumplió el pago pactado."],
    "pruebas": "Pagaré original y contrato de suministro.",
    "fundamentos_derecho": "Artículos 422 y siguientes del Código General del Proceso.",
    "notif_demandante_direccion": "Calle 10 # 5-20, Cali",
    "notif_demandante_email": "notificaciones@andina.com",
    "notif_apoderado_email": "camila@despacho.com",
    "notif_demandado_direccion": "Carrera 7 # 71-21, Bogotá",
}


class Articulo82Tests(APITestCase):
    def setUp(self):
        self.abogado = crear_usuario("abog1", "abogado")
        self.client.force_authenticate(self.abogado)

    def crear(self, **extra):
        d = dict(COMPLETA)
        d.update(extra)
        return self.client.post("/api/demandas/", d, format="json")

    def test_demanda_completa_cumple_todos_los_numerales(self):
        r = self.crear()
        self.assertEqual(r.status_code, 201, r.data)
        req = r.data["requisitos"]
        self.assertEqual(req["cumplidos"], req["total"], [i for i in req["items"] if i["falta"]])
        self.assertEqual(req["total"], 10)  # el numeral 11 es solo informativo
        # el documento se guarda normalizado
        self.assertEqual(r.data["demandante_documento"], "900123456-7")
        self.assertEqual(r.data["apoderado_documento"], "31000000")

    def test_demanda_minima_sigue_siendo_valida_y_muestra_lo_que_falta(self):
        r = self.client.post(
            "/api/demandas/",
            {"clase_proceso": "Ordinario", "demandante": "Ana Pérez", "demandado": "Empresa XYZ",
             "pretensiones": "Pago de prestaciones sociales adeudadas."},
            format="json",
        )
        self.assertEqual(r.status_code, 201, r.data)
        numerales_faltantes = {i["numeral"] for i in r.data["requisitos"]["items"] if i["cumple"] is False}
        self.assertTrue({1, 2, 3, 5, 6, 8, 9, 10} <= numerales_faltantes)
        self.assertNotIn(4, numerales_faltantes)

    def test_persona_juridica_se_identifica_con_nit(self):
        r = self.crear(demandante_tipo_documento="CC", demandante_documento="12345678")
        self.assertEqual(r.status_code, 400)
        self.assertIn("demandante_tipo_documento", r.data)

    def test_formato_de_documentos(self):
        self.assertEqual(self.crear(demandante_documento="123").status_code, 400)  # NIT muy corto
        self.assertEqual(
            self.crear(demandante_tipo_persona="natural", demandante_tipo_documento="CC", demandante_documento="ABC123").status_code, 400
        )
        r = self.crear(demandante_documento="")
        self.assertEqual(r.status_code, 201)
        r = self.crear(demandado_tipo_documento="", demandado_documento="123456789")
        self.assertEqual(r.status_code, 400)  # número sin tipo
        self.assertIn("demandado_documento", r.data)
        self.assertEqual(self.crear(apoderado_documento="12ab").status_code, 400)

    def test_documento_del_demandado_es_opcional(self):
        r = self.crear(demandado_tipo_documento="", demandado_documento="", demandado_tipo_persona="natural", demandado_representante="")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["requisitos"]["cumplidos"], r.data["requisitos"]["total"])

    def test_hechos_se_limpian_y_validan(self):
        r = self.crear(hechos=["  Primer hecho con   espacios  ", "", "   "])
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["hechos"], ["Primer hecho con espacios"])
        self.assertEqual(self.crear(hechos=["ok"]).status_code, 400)
        self.assertEqual(self.crear(hechos="no es lista").status_code, 400)
        self.assertEqual(self.crear(hechos=[123]).status_code, 400)

    def test_correos_invalidos_se_rechazan(self):
        self.assertEqual(self.crear(notif_demandante_email="no-es-correo").status_code, 400)

    def test_domicilio_desconocido_del_demandado_parrafo_1(self):
        r = self.crear(demandado_domicilio="", notif_demandado_direccion="", demandado_ubicacion_desconocida=False)
        faltan = {i["numeral"] for i in r.data["requisitos"]["items"] if i["cumple"] is False}
        self.assertTrue({2, 10} <= faltan)
        r = self.crear(demandado_domicilio="", notif_demandado_direccion="", demandado_ubicacion_desconocida=True)
        self.assertEqual(r.data["requisitos"]["cumplidos"], r.data["requisitos"]["total"])

    def test_sin_apoderado_no_exige_datos_del_apoderado(self):
        r = self.crear(sin_apoderado=True, apoderado_nombre="", apoderado_documento="", apoderado_tarjeta_profesional="", notif_apoderado_email="")
        self.assertEqual(r.data["requisitos"]["cumplidos"], r.data["requisitos"]["total"])

    def test_juramento_estimatorio_y_cuantia_solo_si_aplican(self):
        r = self.crear(requiere_juramento_estimatorio=True, juramento_estimatorio="")
        self.assertIn(7, {i["numeral"] for i in r.data["requisitos"]["items"] if i["cumple"] is False})
        r = self.crear(requiere_juramento_estimatorio=True, juramento_estimatorio="Estimo bajo juramento la suma de $5.000.000 por perjuicios.")
        self.assertTrue(next(i for i in r.data["requisitos"]["items"] if i["numeral"] == 7)["cumple"])
        r = self.crear(cuantia="0", cuantia_aplica=True)
        self.assertIn(9, {i["numeral"] for i in r.data["requisitos"]["items"] if i["cumple"] is False})
        r = self.crear(cuantia="0", cuantia_aplica=False)
        self.assertTrue(next(i for i in r.data["requisitos"]["items"] if i["numeral"] == 9)["cumple"])

    def test_borrador_sigue_los_numerales_del_articulo_82(self):
        pk = self.crear().data["id"]
        texto = self.client.get(f"/api/demandas/{pk}/generar-borrador/").data["borrador"]
        self.assertIn("JUEZ CIVIL DEL CIRCUITO DE CALI (REPARTO)", texto)
        self.assertIn("NIT 900123456-7", texto)
        self.assertIn("1. El 1 de marzo de 2025 las partes suscribieron el contrato.", texto)
        self.assertIn("2. El demandado incumplió el pago pactado.", texto)
        self.assertIn("T.P. 123456", texto)
        self.assertIn("(numeral 10)", texto)
        self.assertIn("parágrafo 2", texto)

    def test_borrador_marca_lo_que_falta_y_la_ubicacion_desconocida(self):
        pk = self.crear(hechos=[], pruebas="", demandado_ubicacion_desconocida=True, demandado_domicilio="").data["id"]
        texto = self.client.get(f"/api/demandas/{pk}/generar-borrador/").data["borrador"]
        self.assertIn("[Hecho primero.]", texto)
        self.assertIn("de domicilio desconocido", texto)
        self.assertIn("se desconoce el lugar donde recibirá notificaciones", texto)

    def test_edicion_parcial_conserva_los_demas_campos(self):
        pk = self.crear().data["id"]
        r = self.client.patch(f"/api/demandas/{pk}/", {"fundamentos_derecho": "Artículo 82 del CGP."}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["demandante_documento"], "900123456-7")
        self.assertEqual(len(r.data["hechos"]), 2)


COMPLETA96 = {
    "clase_proceso": "Ejecutivo singular",
    "demandante": "Comercializadora Andina S.A.S.",
    "demandado": "Constructora Horizonte Ltda.",
    "demandado_tipo_persona": "juridica",
    "demandado_tipo_documento": "NIT",
    "demandado_documento": "800765432-1",
    "demandado_domicilio": "Bogotá D.C.",
    "demandado_representante": "Marta Lucía Gómez Rojas",
    "demandado_representante_documento": "C.C. 52000111",
    "apoderado_nombre": "Camila Herrera Gonzales",
    "apoderado_documento": "31000000",
    "apoderado_tarjeta_profesional": "123456",
    "apoderado_domicilio": "Bogotá D.C.",
    "pronunciamiento_pretensiones": "Me opongo a todas las pretensiones por las razones que se exponen en las excepciones.",
    "pronunciamientos_hechos": [
        {"hecho": "El 15 de febrero de 2026 la demandada suscribió el pagaré No. 001.", "respuesta": "admite", "razones": ""},
        {"hecho": "El pagaré se pactó con vencimiento el 31 de julio de 2026.", "respuesta": "niega",
         "razones": "El vencimiento pactado fue el 31 de diciembre de 2026, según la carta de instrucciones."},
        {"hecho": "A la fecha la demandada no ha pagado el capital.", "respuesta": "no_consta",
         "razones": "El pago fue realizado por un tercero y el demandado no tiene el soporte a la mano."},
    ],
    "excepciones_merito": [
        {"nombre": "Inexigibilidad de la obligación", "fundamento": "La obligación no estaba vencida a la presentación de la demanda."},
    ],
    "pruebas": "Carta de instrucciones y comprobantes de pago.",
    "notif_demandado_direccion": "Carrera 7 # 71-21, Bogotá",
    "notif_demandado_email": "notificaciones@horizonte.com",
    "notif_apoderado_email": "camila.herrera@despacho.com",
    "anexo_poder": True,
    "anexo_existencia_representacion": True,
}


class Articulo96Tests(APITestCase):
    def setUp(self):
        self.admin = crear_usuario("admin1", "administrador")
        self.abogado = crear_usuario("abog1", "abogado")
        self.otro = crear_usuario("abog2", "abogado")
        self.client.force_authenticate(self.abogado)

    def crear(self, **extra):
        d = dict(COMPLETA96)
        d.update(extra)
        return self.client.post("/api/contestaciones/", d, format="json")

    def faltan(self, r):
        return {i["numeral"] for i in r.data["requisitos"]["items"] if i["cumple"] is False}

    def test_contestacion_completa_cumple_todos_los_numerales(self):
        r = self.crear()
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["requisitos"]["cumplidos"], r.data["requisitos"]["total"], r.data["requisitos"])
        self.assertEqual(r.data["requisitos"]["total"], 6)

    def test_contestacion_minima_se_guarda_y_lista_lo_que_falta(self):
        r = self.client.post("/api/contestaciones/", {"clase_proceso": "Verbal", "demandante": "Ana Pérez", "demandado": "Empresa XYZ"}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(self.faltan(r), {1, 2, 3, 4, 5, 6})

    def test_hecho_negado_sin_razones_no_cumple(self):
        hechos = [{"hecho": "El contrato terminó el 1 de marzo.", "respuesta": "niega", "razones": ""}]
        r = self.crear(pronunciamientos_hechos=hechos)
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(self.faltan(r), {2})
        faltas = next(i for i in r.data["requisitos"]["items"] if i["numeral"] == 2)["falta"]
        self.assertTrue(any("presumirá cierto" in f for f in faltas))

    def test_hecho_admitido_no_necesita_razones(self):
        hechos = [{"hecho": "El contrato terminó el 1 de marzo.", "respuesta": "admite", "razones": ""}]
        self.assertEqual(self.faltan(self.crear(pronunciamientos_hechos=hechos)), set())

    def test_respuesta_invalida_y_hecho_corto_se_rechazan(self):
        mal = [{"hecho": "El contrato terminó el 1 de marzo.", "respuesta": "tal vez", "razones": ""}]
        self.assertEqual(self.crear(pronunciamientos_hechos=mal).status_code, 400)
        corto = [{"hecho": "ok", "respuesta": "admite", "razones": ""}]
        self.assertEqual(self.crear(pronunciamientos_hechos=corto).status_code, 400)
        self.assertEqual(self.crear(pronunciamientos_hechos="no es lista").status_code, 400)

    def test_renglones_vacios_se_descartan(self):
        vacios = COMPLETA96["pronunciamientos_hechos"] + [{"hecho": "", "respuesta": "", "razones": ""}]
        r = self.crear(pronunciamientos_hechos=vacios)
        self.assertEqual(len(r.data["pronunciamientos_hechos"]), 3)

    def test_excepcion_sin_fundamento_no_cumple_y_sin_excepciones_si(self):
        r = self.crear(excepciones_merito=[{"nombre": "Prescripción", "fundamento": ""}])
        self.assertEqual(self.faltan(r), {3})
        r = self.crear(excepciones_merito=[], sin_excepciones=True)
        self.assertEqual(self.faltan(r), set())
        r = self.crear(excepciones_merito=[{"nombre": "x", "fundamento": "algo"}])
        self.assertEqual(r.status_code, 400)

    def test_juramento_y_retencion_solo_se_exigen_si_se_marcan(self):
        self.assertEqual(self.faltan(self.crear(objeta_juramento_estimatorio=True)), {3})
        self.assertEqual(self.faltan(self.crear(alega_derecho_retencion=True)), {3})
        r = self.crear(objeta_juramento_estimatorio=True, objecion_juramento="Se objeta el valor estimado por exceder lo debido.",
                       alega_derecho_retencion=True, derecho_retencion="Se retiene el bien hasta el pago de las mejoras.")
        self.assertEqual(self.faltan(r), set())

    def test_pruebas_pueden_obrar_ya_en_el_expediente(self):
        self.assertEqual(self.faltan(self.crear(pruebas="", pruebas_en_expediente=True)), set())
        self.assertEqual(self.faltan(self.crear(pruebas="", pruebas_en_expediente=False)), {4})

    def test_demandado_sin_apoderado_no_exige_datos_ni_poder(self):
        r = self.crear(sin_apoderado=True, apoderado_nombre="", apoderado_documento="", apoderado_tarjeta_profesional="",
                       apoderado_domicilio="", anexo_poder=False, notif_apoderado_email="")
        self.assertEqual(self.faltan(r), set())

    def test_apoderado_exige_poder_y_persona_juridica_exige_existencia(self):
        self.assertEqual(self.faltan(self.crear(anexo_poder=False)), {6})
        self.assertEqual(self.faltan(self.crear(anexo_existencia_representacion=False)), {6})

    def test_validacion_de_documentos(self):
        self.assertEqual(self.crear(demandado_documento="123").status_code, 400)  # NIT de 3 dígitos
        self.assertEqual(self.crear(demandado_tipo_documento="CC").status_code, 400)  # jurídica con CC
        self.assertEqual(self.crear(apoderado_documento="abc").status_code, 400)
        self.assertEqual(self.crear(notif_demandado_email="notificaciones").status_code, 400)
        r = self.crear(demandado_documento="800.765.432-1")
        self.assertEqual(r.data["demandado_documento"], "800765432-1")

    def test_borrador_sigue_los_numerales_del_articulo_96(self):
        pk = self.crear().data["id"]
        texto = self.client.get(f"/api/contestaciones/{pk}/generar-borrador/").data["borrador"]
        for esperado in (
            "NIT 800765432-1", "AL HECHO 1: SE ADMITE.", "AL HECHO 2: NO ES CIERTO.", "AL HECHO 3: NO ME CONSTA.",
            "El vencimiento pactado fue el 31 de diciembre de 2026", "INEXIGIBILIDAD DE LA OBLIGACIÓN",
            "No se formula objeción al juramento estimatorio", "T.P. 123456", "Certificado de existencia y representación",
            "V. NOTIFICACIONES",
        ):
            self.assertIn(esperado, texto)

    def test_borrador_marca_lo_que_falta(self):
        pk = self.client.post("/api/contestaciones/", {"clase_proceso": "Verbal", "demandante": "Ana Pérez", "demandado": "Empresa XYZ"}, format="json").data["id"]
        texto = self.client.get(f"/api/contestaciones/{pk}/generar-borrador/").data["borrador"]
        self.assertIn("[Pronúnciese sobre cada hecho", texto)
        self.assertIn("[Excepciones de mérito", texto)

    def test_vincular_demanda_respeta_el_alcance(self):
        ajena = Demanda.objects.create(clase_proceso="Verbal", demandante="A B", demandado="C D", pretensiones="Pretensiones de prueba.",
                                       abogado_responsable=self.otro)
        propia = Demanda.objects.create(clase_proceso="Verbal", demandante="A B", demandado="C D", pretensiones="Pretensiones de prueba.",
                                        abogado_responsable=self.abogado)
        self.assertEqual(self.crear(demanda=ajena.pk).status_code, 400)
        r = self.crear(demanda=propia.pk)
        self.assertEqual(r.status_code, 201, r.data)
        self.assertIn("Verbal", r.data["demanda_texto"])
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.crear(demanda=ajena.pk).status_code, 201)

    def test_presentada_con_requisitos_incompletos_se_guarda_y_avisa(self):
        r = self.client.post("/api/contestaciones/", {
            "clase_proceso": "Verbal", "demandante": "Ana Pérez", "demandado": "Empresa XYZ", "estado": "presentada",
            "fecha_notificacion": (timezone.localdate() - timedelta(days=5)).isoformat(),
            "fecha_presentacion": timezone.localdate().isoformat(),
        }, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertLess(r.data["requisitos"]["cumplidos"], r.data["requisitos"]["total"])
