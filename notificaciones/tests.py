from datetime import timedelta

from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APITestCase

from audiencias.models import Audiencia
from core.testutils import crear_cliente, crear_expediente, crear_usuario
from expedientes.models import EtapaProceso
from facturacion.models import Factura
from notificaciones.models import Notificacion
from notificaciones.servicios import generar_para_todos, generar_para_usuario


class GeneracionAutomaticaTests(APITestCase):
    def setUp(self):
        self.hoy = timezone.localdate()
        self.admin = crear_usuario("admin1", "administrador")
        self.abogado = crear_usuario("abog1", "abogado")
        self.otro = crear_usuario("abog2", "abogado")
        self.exp = crear_expediente(self.abogado)
        self.exp_ajeno = crear_expediente(self.otro)

    def mensajes(self, usuario, tipo=None):
        qs = Notificacion.objects.filter(usuario=usuario)
        if tipo:
            qs = qs.filter(tipo=tipo)
        return [n.mensaje for n in qs]

    def test_avisa_de_audiencia_de_manana(self):
        Audiencia.objects.create(expediente=self.exp, fecha_hora=timezone.now() + timedelta(days=1), lugar="Sala 4")
        self.assertEqual(generar_para_usuario(self.abogado), 1)
        mensaje = self.mensajes(self.abogado, "audiencia")[0]
        self.assertIn("mañana", mensaje)
        self.assertIn(self.exp.numero, mensaje)

    def test_no_avisa_de_audiencias_lejanas_ni_ajenas(self):
        Audiencia.objects.create(expediente=self.exp, fecha_hora=timezone.now() + timedelta(days=30), lugar="Sala 4")
        Audiencia.objects.create(expediente=self.exp_ajeno, fecha_hora=timezone.now() + timedelta(days=1), lugar="Sala 5")
        self.assertEqual(generar_para_usuario(self.abogado), 0)

    def test_no_duplica_avisos(self):
        Audiencia.objects.create(expediente=self.exp, fecha_hora=timezone.now() + timedelta(days=1), lugar="Sala 4")
        generar_para_usuario(self.abogado)
        self.assertEqual(generar_para_usuario(self.abogado), 0)
        self.assertEqual(Notificacion.objects.filter(usuario=self.abogado).count(), 1)

    def test_una_audiencia_reprogramada_genera_un_aviso_nuevo(self):
        aud = Audiencia.objects.create(expediente=self.exp, fecha_hora=timezone.now() + timedelta(days=1), lugar="Sala 4")
        generar_para_usuario(self.abogado)
        aud.fecha_hora = timezone.now() + timedelta(days=2)
        aud.save()
        self.assertEqual(generar_para_usuario(self.abogado), 1)

    def test_avisa_de_plazo_proximo_y_de_plazo_vencido(self):
        EtapaProceso.objects.create(expediente=self.exp, nombre="Contestación", fecha_limite=self.hoy + timedelta(days=2))
        EtapaProceso.objects.create(expediente=self.exp, nombre="Notificación", fecha_limite=self.hoy - timedelta(days=4))
        self.assertEqual(generar_para_usuario(self.abogado), 2)
        mensajes = self.mensajes(self.abogado, "plazo")
        self.assertTrue(any("VENCIDO hace 4" in m and "Notificación" in m for m in mensajes))
        self.assertTrue(any("Contestación" in m and "VENCIDO" not in m for m in mensajes))

    def test_no_avisa_de_etapas_completadas_ni_de_expedientes_cerrados(self):
        EtapaProceso.objects.create(
            expediente=self.exp, nombre="Hecha", fecha_limite=self.hoy - timedelta(days=1), estado="completada"
        )
        cerrado = crear_expediente(self.abogado, estado="cerrado")
        EtapaProceso.objects.create(expediente=cerrado, nombre="Vieja", fecha_limite=self.hoy - timedelta(days=1))
        self.assertEqual(generar_para_usuario(self.abogado), 0)

    def test_facturas_vencidas_se_marcan_y_solo_avisan_a_directivos(self):
        fac = Factura.objects.create(
            numero="F-1", expediente=self.exp, cliente=crear_cliente(), concepto="Honorarios", monto=1000,
            fecha_vencimiento=self.hoy - timedelta(days=3),
        )
        self.assertEqual(generar_para_usuario(self.abogado), 0)  # el abogado no recibe avisos de facturación
        fac.refresh_from_db()
        self.assertEqual(fac.estado, "vencida")  # pero la factura ya quedó marcada como vencida

        self.assertEqual(generar_para_usuario(self.admin), 1)
        self.assertIn("VENCIDA", self.mensajes(self.admin, "factura")[0])

    def test_factura_proxima_a_vencer(self):
        Factura.objects.create(
            numero="F-2", expediente=self.exp, concepto="Honorarios", monto=1000,
            fecha_vencimiento=self.hoy + timedelta(days=2),
        )
        self.assertEqual(generar_para_usuario(self.admin), 1)
        self.assertIn("vence", self.mensajes(self.admin, "factura")[0])

    def test_generar_para_todos_y_comando(self):
        Audiencia.objects.create(expediente=self.exp, fecha_hora=timezone.now() + timedelta(days=1), lugar="Sala 4")
        Audiencia.objects.create(expediente=self.exp_ajeno, fecha_hora=timezone.now() + timedelta(days=1), lugar="Sala 5")
        self.assertEqual(generar_para_todos(), 2)
        call_command("generar_notificaciones")  # idempotente
        self.assertEqual(Notificacion.objects.count(), 2)


class NotificacionApiTests(APITestCase):
    def setUp(self):
        self.abogado = crear_usuario("abog1", "abogado")
        self.otro = crear_usuario("abog2", "abogado")
        self.exp = crear_expediente(self.abogado)

    def test_al_listar_se_generan_los_avisos_pendientes(self):
        EtapaProceso.objects.create(
            expediente=self.exp, nombre="Contestación", fecha_limite=timezone.localdate() + timedelta(days=1)
        )
        self.client.force_authenticate(self.abogado)
        r = self.client.get("/api/notificaciones/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data), 1)
        self.assertEqual(r.data[0]["tipo"], "plazo")
        # Una segunda consulta no duplica
        self.assertEqual(len(self.client.get("/api/notificaciones/").data), 1)

    def test_cada_usuario_ve_solo_las_suyas(self):
        Notificacion.objects.create(usuario=self.otro, tipo="general", mensaje="Ajena")
        self.client.force_authenticate(self.abogado)
        self.assertEqual(self.client.get("/api/notificaciones/").data, [])

    def test_marcar_como_leida(self):
        n = Notificacion.objects.create(usuario=self.abogado, tipo="general", mensaje="Hola")
        self.client.force_authenticate(self.abogado)
        r = self.client.patch(f"/api/notificaciones/{n.pk}/", {"leida": True}, format="json")
        self.assertEqual(r.status_code, 200)
        n.refresh_from_db()
        self.assertTrue(n.leida)

    def test_la_clave_no_se_puede_modificar_desde_la_api(self):
        n = Notificacion.objects.create(usuario=self.abogado, tipo="general", mensaje="Hola", clave="x")
        self.client.force_authenticate(self.abogado)
        self.client.patch(f"/api/notificaciones/{n.pk}/", {"clave": "otra"}, format="json")
        n.refresh_from_db()
        self.assertEqual(n.clave, "x")
