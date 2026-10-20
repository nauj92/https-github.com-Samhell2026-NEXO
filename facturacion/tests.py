from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase

from core.testutils import crear_cliente, crear_expediente, crear_usuario
from facturacion.models import Factura


class FacturaApiTests(APITestCase):
    def setUp(self):
        self.admin = crear_usuario("admin1", "administrador")
        self.abogado = crear_usuario("abog1", "abogado")
        self.otro = crear_usuario("abog2", "abogado")
        self.cliente = crear_cliente("Cliente Uno")
        self.exp = crear_expediente(self.abogado, cliente=self.cliente)
        self.exp_ajeno = crear_expediente(self.otro)
        self.hoy = timezone.localdate()

    def datos(self, **extra):
        d = {
            "numero": "f-100",
            "expediente": self.exp.pk,
            "concepto": "Honorarios etapa inicial",
            "monto": "1500000.00",
            "estado": "pendiente",
            "fecha_vencimiento": (self.hoy + timedelta(days=10)).isoformat(),
        }
        d.update(extra)
        return d

    def post(self, **extra):
        return self.client.post("/api/facturas/", self.datos(**extra), format="json")

    def test_crea_factura_normaliza_numero_y_completa_cliente(self):
        self.client.force_authenticate(self.abogado)
        r = self.post()
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["numero"], "F-100")
        self.assertEqual(r.data["cliente"], self.cliente.pk)  # tomado del expediente
        self.assertEqual(r.data["cliente_nombre"], "Cliente Uno")

    def test_monto_debe_ser_positivo(self):
        self.client.force_authenticate(self.abogado)
        for monto in ("0", "-5000"):
            r = self.post(monto=monto)
            self.assertEqual(r.status_code, 400)
            self.assertIn("mayor que cero", str(r.data["monto"][0]))

    def test_vencimiento_no_puede_ser_anterior_a_la_emision(self):
        self.client.force_authenticate(self.abogado)
        r = self.post(fecha_vencimiento=(self.hoy - timedelta(days=1)).isoformat())
        self.assertEqual(r.status_code, 400)
        self.assertIn("fecha_vencimiento", r.data)

    def test_el_cliente_debe_coincidir_con_el_del_expediente(self):
        self.client.force_authenticate(self.abogado)
        r = self.post(cliente=crear_cliente("Otro Cliente").pk)
        self.assertEqual(r.status_code, 400)
        self.assertIn("cliente", r.data)

    def test_abogado_debe_asociar_la_factura_a_un_expediente(self):
        self.client.force_authenticate(self.abogado)
        r = self.post(expediente=None)
        self.assertEqual(r.status_code, 400)
        self.assertIn("expediente", r.data)

    def test_admin_puede_facturar_sin_expediente(self):
        self.client.force_authenticate(self.admin)
        r = self.post(expediente=None, cliente=self.cliente.pk)
        self.assertEqual(r.status_code, 201, r.data)

    def test_no_se_factura_sobre_expediente_ajeno(self):
        self.client.force_authenticate(self.abogado)
        self.assertEqual(self.post(expediente=self.exp_ajeno.pk).status_code, 400)

    def test_cada_usuario_ve_solo_sus_facturas(self):
        Factura.objects.create(numero="A-1", expediente=self.exp, concepto="Propia", monto=100)
        Factura.objects.create(numero="B-1", expediente=self.exp_ajeno, concepto="Ajena", monto=100)
        self.client.force_authenticate(self.abogado)
        self.assertEqual([f["numero"] for f in self.client.get("/api/facturas/").data], ["A-1"])
        self.client.force_authenticate(self.admin)
        self.assertEqual(len(self.client.get("/api/facturas/").data), 2)

    def test_fecha_de_pago_se_fija_y_se_borra_sola(self):
        self.client.force_authenticate(self.abogado)
        creada = self.post().data
        self.assertIsNone(creada["fecha_pago"])

        pagada = self.client.patch(f"/api/facturas/{creada['id']}/", {"estado": "pagada"}, format="json").data
        self.assertEqual(pagada["fecha_pago"], self.hoy.isoformat())

        vuelta = self.client.patch(f"/api/facturas/{creada['id']}/", {"estado": "pendiente"}, format="json").data
        self.assertIsNone(vuelta["fecha_pago"])

    def test_la_fecha_de_pago_no_se_puede_enviar_a_mano(self):
        self.client.force_authenticate(self.abogado)
        r = self.post(fecha_pago="2020-01-01")
        self.assertIsNone(r.data["fecha_pago"])

    def test_numero_repetido(self):
        self.client.force_authenticate(self.abogado)
        self.assertEqual(self.post().status_code, 201)
        self.assertEqual(self.post().status_code, 400)
