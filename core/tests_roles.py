"""Pruebas de la matriz de roles y permisos del ingeniero (ver core/permisos.py)."""
from rest_framework.test import APITestCase

from clientes.models import Cliente
from core.permisos import MATRIZ, permisos_de, puede
from core.testutils import crear_cliente, crear_expediente, crear_juzgado, crear_usuario, radicado


class MatrizTests(APITestCase):
    def test_roles_y_letras_de_la_matriz(self):
        admin = crear_usuario("adm", "administrador")
        abogado = crear_usuario("abo", "abogado")
        secretaria = crear_usuario("sec", "secretario_juridico")
        escribiente = crear_usuario("esc", "escribiente")
        dependiente = crear_usuario("dep", "dependiente")
        cliente = crear_usuario("cli", "cliente")
        self.assertTrue(puede(admin, "usuarios", "C"))
        self.assertFalse(puede(abogado, "usuarios", "V"))
        self.assertTrue(puede(abogado, "expedientes", "A"))
        self.assertFalse(puede(admin, "expedientes", "A"))
        self.assertTrue(puede(secretaria, "agenda", "X"))
        self.assertFalse(puede(secretaria, "expedientes", "X"))
        self.assertFalse(puede(escribiente, "expedientes", "C"))
        self.assertTrue(puede(escribiente, "documentos", "E"))
        self.assertEqual(permisos_de(dependiente), {"documentos": "C", "agenda": "V"})
        self.assertFalse(puede(cliente, "expedientes", "E"))
        self.assertEqual(set(permisos_de(crear_usuario("root", "abogado", is_superuser=True))), set(MATRIZ))


class AlcanceYAccionesTests(APITestCase):
    def setUp(self):
        self.admin = crear_usuario("adm", "administrador")
        self.socio = crear_usuario("soc", "abogado", es_socio=True)
        self.abogado = crear_usuario("abo", "abogado")
        self.secretaria = crear_usuario("sec", "secretario_juridico")
        self.escribiente = crear_usuario("esc", "escribiente")
        self.dependiente = crear_usuario("dep", "dependiente")
        self.exp = crear_expediente(self.abogado)
        self.exp.colaboradores.add(self.secretaria)
        self.otro = crear_expediente(crear_usuario("abo2", "abogado"))

    def como(self, usuario):
        self.client.force_authenticate(usuario)

    def ids(self, ruta="/api/expedientes/"):
        return sorted(e["id"] for e in self.client.get(ruta).data)

    def test_alcance_por_rol(self):
        self.como(self.socio)
        self.assertEqual(self.ids(), sorted([self.exp.pk, self.otro.pk]))
        self.como(self.abogado)
        self.assertEqual(self.ids(), [self.exp.pk])
        self.como(self.secretaria)
        self.assertEqual(self.ids(), [self.exp.pk])
        self.como(self.escribiente)  # sin expedientes asignados
        self.assertEqual(self.ids(), [])

    def test_dependiente_sin_acceso_a_expedientes_ni_clientes(self):
        self.como(self.dependiente)
        for ruta in ("/api/expedientes/", "/api/clientes/", "/api/facturas/"):
            self.assertEqual(self.client.get(ruta).status_code, 403, ruta)

    def test_solo_el_administrador_elimina(self):
        cliente = crear_cliente("Para borrar")
        for usuario in (self.abogado, self.secretaria):
            self.como(usuario)
            self.assertEqual(self.client.delete(f"/api/clientes/{cliente.pk}/").status_code, 403, usuario.username)
        self.como(self.admin)
        self.assertEqual(self.client.delete(f"/api/clientes/{cliente.pk}/").status_code, 204)
        self.assertFalse(Cliente.objects.filter(pk=cliente.pk).exists())

    def test_escribiente_solo_consulta_clientes_y_expedientes(self):
        self.exp.colaboradores.add(self.escribiente)
        self.como(self.escribiente)
        self.assertEqual(self.client.get("/api/clientes/").status_code, 200)
        r = self.client.post("/api/clientes/", {"nombre": "X", "tipo_documento": "CC", "numero_documento": "123"}, format="json")
        self.assertEqual(r.status_code, 403)
        r = self.client.patch(f"/api/expedientes/{self.exp.pk}/", {"materia": "Civil"}, format="json")
        self.assertEqual(r.status_code, 403)

    def datos_expediente(self, **extra):
        d = {
            "numero": radicado(), "juzgado": crear_juzgado().pk, "demandante": "Ana", "demandado": "Empresa",
            "materia": "Civil", "estado": "activo",
        }
        d.update(extra)
        return d

    def test_secretaria_crea_expediente_con_abogado_y_lo_sigue_viendo(self):
        self.como(self.secretaria)
        r = self.client.post("/api/expedientes/", self.datos_expediente(), format="json")
        self.assertEqual(r.status_code, 400, "debe indicar el abogado")
        r = self.client.post("/api/expedientes/", self.datos_expediente(abogado_asignado=self.abogado.pk), format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertIn(r.data["id"], self.ids())

    def test_el_responsable_debe_ser_abogado(self):
        self.como(self.admin)
        r = self.client.post("/api/expedientes/", self.datos_expediente(abogado_asignado=self.admin.pk), format="json")
        self.assertEqual(r.status_code, 400)

    def test_secretaria_no_cambia_abogado_ni_estado(self):
        self.como(self.secretaria)
        r = self.client.patch(f"/api/expedientes/{self.exp.pk}/", {"abogado_asignado": self.socio.pk}, format="json")
        self.assertEqual(r.status_code, 400)
        r = self.client.patch(f"/api/expedientes/{self.exp.pk}/", {"estado": "archivado"}, format="json")
        self.assertEqual(r.status_code, 400)
        r = self.client.patch(f"/api/expedientes/{self.exp.pk}/", {"demandante": "Nuevo nombre"}, format="json")
        self.assertEqual(r.status_code, 200, r.data)

    def test_equipo_de_apoyo_solo_secretarias_y_escribientes(self):
        self.como(self.socio)
        r = self.client.patch(f"/api/expedientes/{self.exp.pk}/", {"colaboradores": [self.escribiente.pk]}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        r = self.client.patch(f"/api/expedientes/{self.exp.pk}/", {"colaboradores": [self.dependiente.pk]}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_dashboard_solo_con_permiso_de_reportes(self):
        for usuario, esperado in ((self.admin, 200), (self.abogado, 200), (self.secretaria, 200), (self.escribiente, 403)):
            self.como(usuario)
            self.assertEqual(self.client.get("/api/dashboard/resumen/").status_code, esperado, usuario.username)

    def test_lista_de_abogados_excluye_a_los_demas_roles(self):
        self.como(self.secretaria)
        roles = {u["rol"] for u in self.client.get("/api/usuarios/").data}
        self.assertEqual(roles, {"abogado"})
