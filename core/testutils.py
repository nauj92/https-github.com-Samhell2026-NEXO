"""Ayudas compartidas por las pruebas automatizadas."""
from itertools import count

from django.contrib.auth import get_user_model

from clientes.models import Cliente
from expedientes.models import Expediente, Juzgado

CLAVE = "Clave-Segura-2026"
_consecutivo = count(1)
_documento = count(10000001)


def radicado(anio=2025):
    """Radicado válido de 23 dígitos, distinto en cada llamada."""
    return f"110013103012{anio}{next(_consecutivo):05d}00"


def crear_usuario(username, rol="abogado", **extra):
    return get_user_model().objects.create_user(
        username=username,
        password=CLAVE,
        rol=rol,
        email=f"{username}@example.com",
        first_name=username.capitalize(),
        last_name="Prueba",
        **extra,
    )


def crear_juzgado(nombre="Juzgado 12 Civil del Circuito de Bogotá"):
    return Juzgado.objects.get_or_create(nombre=nombre, defaults={"ciudad": "Bogotá D.C.", "materia": "civil"})[0]


def crear_cliente(nombre="Cliente de Prueba"):
    return Cliente.objects.create(nombre=nombre, tipo_documento="CC", numero_documento=str(next(_documento)))


def crear_expediente(abogado, cliente=None, estado="activo", **extra):
    datos = {
        "numero": radicado(),
        "juzgado": crear_juzgado(),
        "cliente": cliente,
        "demandante": "Demandante de Prueba",
        "demandado": "Demandado de Prueba",
        "materia": "Civil",
        "estado": estado,
        "abogado_asignado": abogado,
    }
    datos.update(extra)
    return Expediente.objects.create(**datos)
