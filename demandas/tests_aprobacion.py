from rest_framework.test import APITestCase

from core.testutils import crear_expediente, crear_usuario
from notificaciones.models import Notificacion

from .models import Citacion

DEMANDA = {
    "clase_proceso": "Ejecutivo singular", "demandante": "Ana Pérez", "demandado": "Luis Gómez",
    "pretensiones": "Pago de la obligación contenida en el pagaré",
}


class AprobacionTests(APITestCase):
    def setUp(self):
        self.abogado = crear_usuario("abo", "abogado")
        self.escribiente = crear_usuario("esc", "escribiente")
        self.dependiente = crear_usuario("dep", "dependiente")
        self.exp = crear_expediente(self.abogado)
        self.exp.colaboradores.add(self.escribiente)

    def como(self, usuario):
        self.client.force_authenticate(usuario)

    def borrador_del_escribiente(self):
        self.como(self.escribiente)
        r = self.client.post(
            "/api/demandas/", {**DEMANDA, "expediente": self.exp.pk, "abogado_responsable": self.abogado.pk}, format="json"
        )
        self.assertEqual(r.status_code, 201, r.data)
        return r.data

    def test_lo_del_abogado_nace_aprobado(self):
        self.como(self.abogado)
        r = self.client.post("/api/demandas/", DEMANDA, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["aprobacion"], "aprobado")
        self.assertEqual(r.data["aprobado_por"], self.abogado.pk)

    def test_lo_del_escribiente_nace_borrador(self):
        self.assertEqual(self.borrador_del_escribiente()["aprobacion"], "borrador")

    def test_dependiente_no_redacta_escritos(self):
        self.como(self.dependiente)
        self.assertEqual(self.client.post("/api/demandas/", DEMANDA, format="json").status_code, 403)

    def test_flujo_enviar_y_aprobar(self):
        demanda = self.borrador_del_escribiente()
        r = self.client.post(f"/api/demandas/{demanda['id']}/enviar/")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["aprobacion"], "pendiente")
        self.assertTrue(Notificacion.objects.filter(usuario=self.abogado, tipo="borrador").exists())
        # el escribiente no puede aprobar
        self.assertEqual(self.client.post(f"/api/demandas/{demanda['id']}/aprobar/").status_code, 403)
        self.como(self.abogado)
        r = self.client.post(f"/api/demandas/{demanda['id']}/aprobar/")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["aprobacion"], "aprobado")
        self.assertTrue(Notificacion.objects.filter(usuario=self.escribiente, tipo="borrador").exists())

    def test_devolver_exige_motivo_y_permite_reenviar(self):
        demanda = self.borrador_del_escribiente()
        self.client.post(f"/api/demandas/{demanda['id']}/enviar/")
        self.como(self.abogado)
        self.assertEqual(self.client.post(f"/api/demandas/{demanda['id']}/devolver/", {}, format="json").status_code, 400)
        r = self.client.post(f"/api/demandas/{demanda['id']}/devolver/", {"motivo": "Falta el hecho 3"}, format="json")
        self.assertEqual(r.data["aprobacion"], "devuelto")
        self.assertEqual(r.data["motivo_devolucion"], "Falta el hecho 3")
        self.como(self.escribiente)
        r = self.client.post(f"/api/demandas/{demanda['id']}/enviar/")
        self.assertEqual(r.data["aprobacion"], "pendiente")

    def test_modificar_un_aprobado_sin_ser_abogado_lo_devuelve_a_borrador(self):
        demanda = self.borrador_del_escribiente()
        self.client.post(f"/api/demandas/{demanda['id']}/enviar/")
        self.como(self.abogado)
        self.client.post(f"/api/demandas/{demanda['id']}/aprobar/")
        self.como(self.escribiente)
        r = self.client.patch(f"/api/demandas/{demanda['id']}/", {"observaciones": "ajuste"}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["aprobacion"], "borrador")
        self.assertIsNone(r.data["aprobado_por"])

    def test_no_se_edita_el_estado_de_aprobacion_a_mano(self):
        demanda = self.borrador_del_escribiente()
        r = self.client.patch(f"/api/demandas/{demanda['id']}/", {"aprobacion": "aprobado"}, format="json")
        self.assertEqual(r.data["aprobacion"], "borrador")

    def test_sin_aprobar_no_se_puede_radicar(self):
        demanda = self.borrador_del_escribiente()
        r = self.client.patch(
            f"/api/demandas/{demanda['id']}/", {"estado": "radicada", "fecha_radicacion": "2025-01-10"}, format="json"
        )
        self.assertEqual(r.status_code, 400)

    def test_contestacion_y_citacion_tienen_el_mismo_flujo(self):
        self.como(self.escribiente)
        r = self.client.post(
            "/api/citaciones/",
            {"destinatario": "Luis Gómez", "expediente": self.exp.pk, "abogado_responsable": self.abogado.pk},
            format="json",
        )
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["aprobacion"], "borrador")
        self.assertEqual(self.client.post(f"/api/citaciones/{r.data['id']}/enviar/").data["aprobacion"], "pendiente")
        self.como(self.abogado)
        self.assertEqual(self.client.post(f"/api/citaciones/{r.data['id']}/aprobar/").data["aprobacion"], "aprobado")
        self.assertEqual(Citacion.objects.get().aprobacion, "aprobado")

    def test_enviar_dos_veces_falla(self):
        demanda = self.borrador_del_escribiente()
        self.client.post(f"/api/demandas/{demanda['id']}/enviar/")
        self.assertEqual(self.client.post(f"/api/demandas/{demanda['id']}/enviar/").status_code, 400)
