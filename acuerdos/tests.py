from datetime import date, timedelta
from decimal import Decimal

from django.test import SimpleTestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from acuerdos.models import AcuerdoPago
from acuerdos.serializers import repartir, sumar_meses
from core.testutils import crear_expediente, crear_usuario

URL = "/api/acuerdos-pago/"


class CalculoCuotasTests(SimpleTestCase):
    def test_reparto_suma_exactamente_el_total(self):
        valores = repartir(Decimal("1000000.00"), 3)
        self.assertEqual(sum(valores), Decimal("1000000.00"))
        self.assertEqual(valores[0], Decimal("333333.33"))
        self.assertEqual(valores[-1], Decimal("333333.34"))

    def test_una_sola_cuota(self):
        self.assertEqual(repartir(Decimal("500.00"), 1), [Decimal("500.00")])

    def test_meses_con_menos_dias(self):
        self.assertEqual(sumar_meses(date(2026, 1, 31), 1), date(2026, 2, 28))
        self.assertEqual(sumar_meses(date(2026, 1, 31), 2), date(2026, 3, 31))
        self.assertEqual(sumar_meses(date(2026, 11, 15), 3), date(2027, 2, 15))


class AcuerdoPagoApiTests(APITestCase):
    def setUp(self):
        self.admin = crear_usuario("admin1", "administrador")
        self.abogado = crear_usuario("abog1", "abogado")
        self.otro = crear_usuario("abog2", "abogado")
        self.cliente_rol = crear_usuario("cli1", "cliente")
        self.exp = crear_expediente(self.abogado)
        self.exp_ajeno = crear_expediente(self.otro)
        self.hoy = timezone.localdate()

    def datos(self, **extra):
        d = {
            "expediente": self.exp.pk, "deudor": "Daniel Rojas", "concepto": "Pago de condena",
            "valor_total": "3000000", "fecha_acuerdo": self.hoy.isoformat(),
            "num_cuotas": 3, "fecha_primera_cuota": (self.hoy + timedelta(days=10)).isoformat(),
        }
        d.update(extra)
        return d

    def crear(self, **extra):
        return self.client.post(URL, self.datos(**extra), format="json")

    def test_exige_autenticacion(self):
        self.assertEqual(self.client.get(URL).status_code, 401)

    def test_crea_con_cuotas_mensuales(self):
        self.client.force_authenticate(self.abogado)
        r = self.crear()
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(len(r.data["cuotas"]), 3)
        self.assertEqual([c["numero"] for c in r.data["cuotas"]], [1, 2, 3])
        self.assertEqual(Decimal(r.data["saldo"]), Decimal("3000000"))
        self.assertEqual(r.data["estado_actual"], "vigente")
        self.assertEqual(AcuerdoPago.objects.get().creado_por, self.abogado)

    def test_valida_datos(self):
        self.client.force_authenticate(self.abogado)
        self.assertEqual(self.crear(valor_total="0").status_code, 400)
        self.assertEqual(self.crear(deudor="  ").status_code, 400)
        self.assertEqual(self.crear(num_cuotas=0).status_code, 400)
        self.assertEqual(self.crear(num_cuotas=121).status_code, 400)
        self.assertEqual(self.crear(fecha_primera_cuota=(self.hoy - timedelta(days=5)).isoformat()).status_code, 400)
        datos = self.datos()
        del datos["num_cuotas"]
        self.assertEqual(self.client.post(URL, datos, format="json").status_code, 400)

    def test_no_permite_expediente_ajeno_ni_cerrado(self):
        self.client.force_authenticate(self.abogado)
        self.assertEqual(self.crear(expediente=self.exp_ajeno.pk).status_code, 400)
        self.exp.estado = "cerrado"
        self.exp.save()
        self.assertEqual(self.crear().status_code, 400)

    def test_cada_usuario_ve_solo_los_suyos(self):
        self.client.force_authenticate(self.abogado)
        self.crear()
        self.client.force_authenticate(self.otro)
        self.assertEqual(len(self.client.get(URL).data), 0)
        self.client.force_authenticate(self.admin)
        self.assertEqual(len(self.client.get(URL).data), 1)

    def test_rol_cliente_no_accede(self):
        self.client.force_authenticate(self.cliente_rol)
        self.assertEqual(self.client.get(URL).status_code, 403)

    def test_filtra_por_expediente(self):
        self.client.force_authenticate(self.admin)
        self.crear()
        self.crear(expediente=self.exp_ajeno.pk)
        self.assertEqual(len(self.client.get(URL, {"expediente": self.exp.pk}).data), 1)

    def test_registrar_pago_y_deshacerlo(self):
        self.client.force_authenticate(self.abogado)
        acuerdo = self.crear().data
        c1 = acuerdo["cuotas"][0]["id"]
        r = self.client.post(f"{URL}{acuerdo['id']}/pagar/", {"cuota": c1}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertTrue(r.data["cuotas"][0]["pagada"])
        self.assertEqual(Decimal(r.data["total_pagado"]), Decimal("1000000.00"))
        self.assertEqual(Decimal(r.data["saldo"]), Decimal("2000000.00"))
        # no se paga dos veces
        self.assertEqual(self.client.post(f"{URL}{acuerdo['id']}/pagar/", {"cuota": c1}, format="json").status_code, 400)
        r = self.client.post(f"{URL}{acuerdo['id']}/reabrir/", {"cuota": c1}, format="json")
        self.assertFalse(r.data["cuotas"][0]["pagada"])
        self.assertEqual(Decimal(r.data["saldo"]), Decimal("3000000.00"))
        self.assertEqual(self.client.post(f"{URL}{acuerdo['id']}/reabrir/", {"cuota": c1}, format="json").status_code, 400)

    def test_pago_con_fecha_futura_o_cuota_ajena_se_rechaza(self):
        self.client.force_authenticate(self.abogado)
        a1 = self.crear().data
        a2 = self.crear().data
        futura = (self.hoy + timedelta(days=3)).isoformat()
        self.assertEqual(
            self.client.post(f"{URL}{a1['id']}/pagar/", {"cuota": a1["cuotas"][0]["id"], "fecha_pago": futura}, format="json").status_code, 400
        )
        self.assertEqual(
            self.client.post(f"{URL}{a1['id']}/pagar/", {"cuota": a2["cuotas"][0]["id"]}, format="json").status_code, 400
        )
        self.assertEqual(self.client.post(f"{URL}{a1['id']}/pagar/", {}, format="json").status_code, 400)

    def test_no_se_puede_pagar_en_el_acuerdo_de_otro(self):
        self.client.force_authenticate(self.abogado)
        a = self.crear().data
        self.client.force_authenticate(self.otro)
        r = self.client.post(f"{URL}{a['id']}/pagar/", {"cuota": a["cuotas"][0]["id"]}, format="json")
        self.assertEqual(r.status_code, 404)

    def test_estados_cumplido_mora_y_cancelado(self):
        self.client.force_authenticate(self.abogado)
        a = self.crear(num_cuotas=1, fecha_acuerdo=(self.hoy - timedelta(days=40)).isoformat(),
                       fecha_primera_cuota=(self.hoy - timedelta(days=30)).isoformat()).data
        self.assertEqual(a["estado_actual"], "en_mora")
        self.assertTrue(a["cuotas"][0]["en_mora"])
        r = self.client.post(f"{URL}{a['id']}/pagar/", {"cuota": a["cuotas"][0]["id"]}, format="json")
        self.assertEqual(r.data["estado_actual"], "cumplido")
        b = self.crear().data
        r = self.client.patch(f"{URL}{b['id']}/", {"estado": "cancelado"}, format="json")
        self.assertEqual(r.data["estado_actual"], "cancelado")
        self.assertEqual(
            self.client.post(f"{URL}{b['id']}/pagar/", {"cuota": b["cuotas"][0]["id"]}, format="json").status_code, 400
        )

    def test_edicion_limitada(self):
        self.client.force_authenticate(self.abogado)
        a = self.crear().data
        r = self.client.patch(f"{URL}{a['id']}/", {"concepto": "Honorarios", "observaciones": "Acta 4"}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["concepto"], "Honorarios")
        self.assertEqual(len(r.data["cuotas"]), 3)
        self.assertEqual(self.client.patch(f"{URL}{a['id']}/", {"valor_total": "1"}, format="json").status_code, 400)
        self.assertEqual(self.client.patch(f"{URL}{a['id']}/", {"expediente": self.exp_ajeno.pk}, format="json").status_code, 400)

    def test_eliminar_borra_las_cuotas(self):
        self.client.force_authenticate(self.abogado)
        a = self.crear().data
        self.assertEqual(self.client.delete(f"{URL}{a['id']}/").status_code, 204)
        self.assertEqual(AcuerdoPago.objects.count(), 0)

    def test_los_movimientos_quedan_en_el_historial_del_expediente(self):
        self.client.force_authenticate(self.abogado)
        a = self.crear().data
        self.client.post(f"{URL}{a['id']}/pagar/", {"cuota": a["cuotas"][0]["id"]}, format="json")
        self.client.patch(f"{URL}{a['id']}/", {"estado": "cancelado"}, format="json")
        self.client.delete(f"{URL}{a['id']}/")
        eventos = self.client.get(f"/api/expedientes/{self.exp.pk}/historial/").data
        self.assertEqual(
            [e["tipo"] for e in eventos][:4],
            ["Acuerdo de pago eliminado", "Acuerdo de pago modificado", "Cuota de acuerdo pagada", "Acuerdo de pago registrado"],
        )
        self.assertEqual(eventos[3]["cambios"][0]["nuevo"], "Pago de condena · $3.000.000")
        self.assertEqual(eventos[2]["cambios"][0]["campo"], "Acuerdo «Pago de condena» · Cuota 1 ($1.000.000)")
