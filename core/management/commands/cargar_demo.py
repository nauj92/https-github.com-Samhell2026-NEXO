"""Carga datos de demostración realistas y ficticios.

    python manage.py cargar_demo [--password CLAVE]

* Es idempotente: se puede ejecutar varias veces sin duplicar datos.
* Los radicados tienen la estructura real de 23 dígitos; los nombres de partes,
  empresas y teléfonos son inventados.
* Las fechas son relativas a hoy, así que siempre hay audiencias próximas, un
  plazo por vencer, un plazo vencido y facturas pendientes, pagadas y vencidas.
* Con --password (o la variable DEMO_PASSWORD) también crea tres usuarios de
  ejemplo (socio, abogada y secretario) para demostrar el filtro por rol.
  Sin contraseña, todos los expedientes se asignan a un administrador existente.
"""
import os
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from audiencias.models import Audiencia
from clientes.models import Cliente
from core.permisos import ROLES_DIRECTIVOS
from core.plazos import sumar_dias_habiles
from expedientes.models import EtapaProceso, Expediente, Juzgado
from facturacion.models import Factura
from notificaciones.servicios import generar_para_todos

MARCA = "Dato de demostración"


class Command(BaseCommand):
    help = "Carga datos de demostración (ficticios) para mostrar el sistema."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default=os.environ.get("DEMO_PASSWORD", ""),
            help="Contraseña de los usuarios de ejemplo (también se lee de DEMO_PASSWORD).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        Usuario = get_user_model()
        hoy = timezone.localdate()

        socio, abogada, secretario = self._usuarios(Usuario, options["password"])
        if abogada is None:
            admin = (
                Usuario.objects.filter(is_active=True, is_superuser=True).first()
                or Usuario.objects.filter(is_active=True, rol__in=ROLES_DIRECTIVOS).first()
            )
            if admin is None:
                raise CommandError("No hay ningún administrador. Cree uno (createsuperuser) o use --password.")
            socio = abogada = admin

        juzgados = {
            "civil": self._juzgado("Juzgado 12 Civil del Circuito de Bogotá", "Bogotá D.C.", "civil"),
            "laboral": self._juzgado("Juzgado 3 Laboral del Circuito de Medellín", "Medellín", "laboral"),
            "familia": self._juzgado("Juzgado 7 de Familia de Cali", "Cali", "familia"),
            "municipal": self._juzgado("Juzgado 4 Civil Municipal de Bogotá", "Bogotá D.C.", "civil"),
        }

        andina = self._cliente("Inversiones Andina S.A.S.", "NIT", "900100200-3", "6015550101", "contacto@andina.example", "Calle 100 # 15-20, Bogotá")
        marta = self._cliente("Marta Lucía Gómez Ríos", "CC", "43100200", "3005550102", "marta.gomez@example.com", "Carrera 43A # 10-15, Medellín")
        camila = self._cliente("Camila Andrea Quintero", "CC", "52300400", "3105550103", "camila.q@example.com", "Avenida 6N # 25-30, Cali")
        ferreteria = self._cliente("Ferretería El Tornillo Ltda.", "NIT", "800200300-1", "6015550104", "ventas@eltornillo.example", "Carrera 30 # 12-40, Bogotá")

        # Radicados de 23 dígitos: DANE(5) corp(2) esp(2) despacho(3) año(4) consecutivo(5) recurso(2)
        exp1 = self._expediente("11001310301220250012300", juzgados["civil"], andina, "Inversiones Andina S.A.S.", "Constructora Horizonte Ltda.", "Civil", "activo", abogada)
        exp2 = self._expediente("05001310500320260004500", juzgados["laboral"], marta, "Marta Lucía Gómez Ríos", "Textiles del Valle S.A.", "Laboral", "tramite", abogada)
        exp3 = self._expediente("76001311000720250078100", juzgados["familia"], camila, "Camila Andrea Quintero", "Julián Esteban Ramos", "Familia", "activo", socio)
        exp4 = self._expediente("11001400300420240156700", juzgados["municipal"], ferreteria, "Ferretería El Tornillo Ltda.", "Distribuciones Norte S.A.S.", "Civil", "cerrado", abogada)

        # Etapas (la fecha límite de "Contestación" cae dentro del aviso de 3 días; la de "Notificación" ya venció)
        self._etapa(exp1, "Demanda", "completada", hoy - timedelta(days=40), 1)
        self._etapa(exp1, "Contestación de la demanda", "en_curso", sumar_dias_habiles(hoy, 2), 2)
        self._etapa(exp1, "Audiencia inicial", "pendiente", sumar_dias_habiles(hoy, 20), 3)
        self._etapa(exp2, "Notificación a la demandada", "en_curso", hoy - timedelta(days=2), 1)
        self._etapa(exp2, "Audiencia de conciliación", "pendiente", sumar_dias_habiles(hoy, 15), 2)
        self._etapa(exp3, "Admisión de la demanda", "completada", hoy - timedelta(days=15), 1)
        self._etapa(exp3, "Fijación de cuota alimentaria", "pendiente", sumar_dias_habiles(hoy, 30), 2)
        self._etapa(exp4, "Sentencia", "completada", hoy - timedelta(days=90), 1)

        # Audiencias (a horas distintas para no chocar entre sí)
        self._audiencia(exp1, hoy + timedelta(days=2), time(9, 0), "Sala 4, Palacio de Justicia, Bogotá")
        self._audiencia(exp2, hoy + timedelta(days=10), time(10, 30), "Sala de audiencias 2, Medellín")
        self._audiencia(exp3, hoy + timedelta(days=1), time(14, 30), "Juzgado 7 de Familia, Cali")

        # Facturas: pendiente con plazo, pagada y vencida
        self._factura("DEMO-001", exp1, andina, "Honorarios etapa inicial", "4500000", "pendiente", hoy - timedelta(days=5), hoy + timedelta(days=10))
        self._factura("DEMO-002", exp2, marta, "Honorarios de representación", "2800000", "pagada", hoy - timedelta(days=12), hoy - timedelta(days=2), pagada_el=hoy - timedelta(days=3))
        self._factura("DEMO-003", exp3, camila, "Honorarios por asesoría", "1500000", "pendiente", hoy - timedelta(days=30), hoy - timedelta(days=5))

        creadas = generar_para_todos()
        self.stdout.write(self.style.SUCCESS(f"Datos de demostración listos. Notificaciones generadas: {creadas}."))
        if abogada != socio:
            self.stdout.write("Usuarios de ejemplo: socio.herrera, abogada.rojas, secretario.diaz (misma contraseña indicada).")

    # ---- auxiliares -----------------------------------------------------------
    def _usuarios(self, Usuario, password):
        if not password:
            return None, None, None
        datos = [
            ("socio.herrera", "Andrés", "Herrera", "socio_director"),
            ("abogada.rojas", "Laura", "Rojas", "abogado"),
            ("secretario.diaz", "Camilo", "Díaz", "secretario_juridico"),
        ]
        usuarios = []
        for username, nombre, apellido, rol in datos:
            usuario, creado = Usuario.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": nombre,
                    "last_name": apellido,
                    "email": f"{username}@lexerp.example",
                    "rol": rol,
                },
            )
            if creado:
                usuario.set_password(password)
                usuario.save()
            usuarios.append(usuario)
        return tuple(usuarios)

    def _juzgado(self, nombre, ciudad, materia):
        return Juzgado.objects.get_or_create(nombre=nombre, ciudad=ciudad, defaults={"materia": materia})[0]

    def _cliente(self, nombre, tipo, documento, telefono, email, direccion):
        return Cliente.objects.get_or_create(
            numero_documento=documento,
            defaults={"nombre": nombre, "tipo_documento": tipo, "telefono": telefono, "email": email, "direccion": direccion},
        )[0]

    def _expediente(self, numero, juzgado, cliente, demandante, demandado, materia, estado, abogado):
        return Expediente.objects.get_or_create(
            numero=numero,
            defaults={
                "juzgado": juzgado, "cliente": cliente, "demandante": demandante, "demandado": demandado,
                "materia": materia, "estado": estado, "abogado_asignado": abogado,
            },
        )[0]

    def _etapa(self, expediente, nombre, estado, fecha_limite, orden):
        return EtapaProceso.objects.get_or_create(
            expediente=expediente, nombre=nombre,
            defaults={"estado": estado, "fecha_limite": fecha_limite, "orden": orden},
        )[0]

    def _audiencia(self, expediente, dia, hora, lugar):
        if Audiencia.objects.filter(expediente=expediente, observaciones=MARCA).exists():
            return
        fecha = timezone.make_aware(datetime.combine(dia, hora))
        Audiencia.objects.create(expediente=expediente, fecha_hora=fecha, lugar=lugar, observaciones=MARCA)

    def _factura(self, numero, expediente, cliente, concepto, monto, estado, emision, vencimiento, pagada_el=None):
        factura, creada = Factura.objects.get_or_create(
            numero=numero,
            defaults={
                "expediente": expediente, "cliente": cliente, "concepto": concepto, "monto": Decimal(monto),
                "estado": estado, "fecha_vencimiento": vencimiento, "fecha_pago": pagada_el,
            },
        )
        if creada:  # fecha_emision es automática (auto_now_add): se ajusta después de crear
            Factura.objects.filter(pk=factura.pk).update(fecha_emision=emision)
        return factura
