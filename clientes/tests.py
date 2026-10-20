from rest_framework.test import APITestCase

from clientes.models import Cliente
from core.testutils import crear_usuario


class ClienteApiTests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(crear_usuario("abog1", "abogado"))

    def post(self, **extra):
        datos = {"nombre": "María Pérez", "tipo_documento": "CC", "numero_documento": "52123456"}
        datos.update(extra)
        return self.client.post("/api/clientes/", datos, format="json")

    def test_crea_cliente_valido(self):
        r = self.post(telefono="3001234567", email="maria@example.com")
        self.assertEqual(r.status_code, 201, r.data)

    def test_cedula_con_letras_o_longitud_incorrecta(self):
        for numero in ("5212ABC", "123", "12345678901"):
            r = self.post(numero_documento=numero)
            self.assertEqual(r.status_code, 400, numero)
            self.assertIn("numero_documento", r.data)

    def test_cedula_con_puntos_se_normaliza(self):
        r = self.post(numero_documento="52.123.456")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["numero_documento"], "52123456")

    def test_documento_repetido_aunque_cambie_el_formato(self):
        self.assertEqual(self.post().status_code, 201)
        r = self.post(numero_documento="52.123.456")
        self.assertEqual(r.status_code, 400)
        self.assertIn("Ya existe", str(r.data["numero_documento"][0]))

    def test_nit_con_digito_de_verificacion(self):
        r = self.post(tipo_documento="NIT", numero_documento="900.123.456-7", nombre="Empresa Ejemplo S.A.S.")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["numero_documento"], "900123456-7")

    def test_nit_invalido(self):
        self.assertEqual(self.post(tipo_documento="NIT", numero_documento="12345").status_code, 400)

    def test_pasaporte(self):
        r = self.post(tipo_documento="PA", numero_documento="ab123456")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["numero_documento"], "AB123456")
        # También se acepta la palabra completa, que se guarda como PA
        r = self.post(tipo_documento="Pasaporte", numero_documento="xy987654")
        self.assertEqual(r.data["tipo_documento"], "PA")
        self.assertEqual(self.post(tipo_documento="PA", numero_documento="a-1").status_code, 400)

    def test_tipo_de_documento_desconocido(self):
        r = self.post(tipo_documento="XYZ")
        self.assertEqual(r.status_code, 400)
        self.assertIn("tipo_documento", r.data)

    def test_telefono_invalido(self):
        self.assertEqual(self.post(telefono="abc").status_code, 400)
        self.assertEqual(self.post(telefono="123").status_code, 400)

    def test_nombre_muy_corto(self):
        self.assertEqual(self.post(nombre="Al").status_code, 400)

    def test_editar_sin_cambiar_documento_no_se_choca_consigo_mismo(self):
        creado = self.post().data
        r = self.client.patch(f"/api/clientes/{creado['id']}/", {"telefono": "3109876543"}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        r = self.client.patch(
            f"/api/clientes/{creado['id']}/", {"tipo_documento": "CC", "numero_documento": "52123456"}, format="json"
        )
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(Cliente.objects.count(), 1)
