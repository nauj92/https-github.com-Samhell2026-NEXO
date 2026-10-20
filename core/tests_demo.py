from django.core.management import call_command
from django.test import TestCase

from clientes.models import Cliente
from core.testutils import CLAVE, crear_usuario
from expedientes.models import Expediente
from expedientes.validators import validar_radicado
from facturacion.models import Factura
from notificaciones.models import Notificacion
from usuarios.models import Usuario


class CargarDemoTests(TestCase):
    def test_con_usuarios_de_ejemplo_es_idempotente_y_los_radicados_son_validos(self):
        call_command("cargar_demo", password=CLAVE, verbosity=0)
        call_command("cargar_demo", password=CLAVE, verbosity=0)  # segunda vez: no duplica

        self.assertEqual(Expediente.objects.count(), 4)
        self.assertEqual(Cliente.objects.count(), 4)
        self.assertEqual(Factura.objects.count(), 3)
        for exp in Expediente.objects.all():
            self.assertEqual(validar_radicado(exp.numero), exp.numero)
        self.assertEqual(Usuario.objects.filter(rol="abogado").count(), 1)

        # El filtro por rol se puede demostrar: la abogada solo tiene sus 3 expedientes.
        abogada = Usuario.objects.get(username="abogada.rojas")
        self.assertEqual(Expediente.objects.filter(abogado_asignado=abogada).count(), 3)
        self.assertTrue(abogada.check_password(CLAVE))

    def test_genera_notificaciones_y_marca_facturas_vencidas(self):
        call_command("cargar_demo", password=CLAVE, verbosity=0)
        self.assertGreater(Notificacion.objects.count(), 0)
        self.assertTrue(Factura.objects.filter(numero="DEMO-003", estado="vencida").exists())
        self.assertTrue(Factura.objects.filter(numero="DEMO-002", estado="pagada", fecha_pago__isnull=False).exists())

    def test_sin_contrasena_usa_al_administrador_existente(self):
        admin = crear_usuario("root", "administrador", is_superuser=True)
        call_command("cargar_demo", password="", verbosity=0)
        self.assertEqual(Expediente.objects.filter(abogado_asignado=admin).count(), 4)
        self.assertEqual(Usuario.objects.count(), 1)  # no creó usuarios de ejemplo
