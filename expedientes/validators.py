"""Validación del número de radicado de un proceso judicial en Colombia.

El radicado tiene 23 dígitos con esta estructura:

    11001 31 03 012 2025 00123 00
    └─┬─┘ └┬┘└┬┘└┬┘ └┬─┘ └─┬─┘ └┬┘
      │    │  │  │   │     │    └ recurso o instancia (2)
      │    │  │  │   │     └ consecutivo del proceso (5)
      │    │  │  │   └ año de radicación (4)
      │    │  │  └ número del despacho (3)
      │    │  └ especialidad (2): 03 civil, 05 laboral, 10 familia, ...
      │    └ corporación o categoría (2): 31 juzgado de circuito, 40 municipal, ...
      └ código DANE de departamento y municipio (5)

Aquí se valida la forma (23 dígitos, año plausible, campos no en cero). No se
consulta si el radicado existe en la Rama Judicial.
"""
import re
from datetime import date

from django.core.exceptions import ValidationError

LONGITUD_RADICADO = 23


def normalizar_radicado(valor):
    """Quita espacios, guiones y puntos: '11001 31 03 012 2025-00123-00' -> solo dígitos."""
    return re.sub(r"[\s.\-]", "", str(valor or ""))


def desglosar_radicado(numero):
    """Devuelve las partes del radicado (el número debe estar normalizado y ser válido)."""
    return {
        "divipola": numero[0:5],
        "corporacion": numero[5:7],
        "especialidad": numero[7:9],
        "despacho": numero[9:12],
        "anio": numero[12:16],
        "consecutivo": numero[16:21],
        "recurso": numero[21:23],
    }


def validar_radicado(valor):
    """Valida el radicado y lo devuelve normalizado (solo dígitos).

    Lanza django.core.exceptions.ValidationError con un mensaje claro en español.
    """
    numero = normalizar_radicado(valor)
    if not numero.isdigit():
        raise ValidationError(
            "El radicado solo puede contener números (se aceptan espacios y guiones como separadores)."
        )
    if len(numero) != LONGITUD_RADICADO:
        raise ValidationError(
            f"El radicado debe tener exactamente {LONGITUD_RADICADO} dígitos y tiene {len(numero)}. "
            "Ejemplo: 11001 31 03 012 2025 00123 00."
        )
    partes = desglosar_radicado(numero)
    anio = int(partes["anio"])
    if not 1900 <= anio <= date.today().year:
        raise ValidationError(
            f"El año del radicado ({partes['anio']}, dígitos 13 a 16) no es válido."
        )
    if int(partes["divipola"]) == 0:
        raise ValidationError("El código de departamento y municipio (dígitos 1 a 5) no puede ser cero.")
    if int(partes["despacho"]) == 0:
        raise ValidationError("El número de despacho (dígitos 10 a 12) no puede ser cero.")
    if int(partes["consecutivo"]) == 0:
        raise ValidationError("El consecutivo del proceso (dígitos 17 a 21) no puede ser cero.")
    return numero


def formatear_radicado(numero):
    """11001310301220250012300 -> '11001 31 03 012 2025 00123 00' (para mostrar)."""
    if len(numero) != LONGITUD_RADICADO or not numero.isdigit():
        return numero
    p = desglosar_radicado(numero)
    return " ".join(p[k] for k in ("divipola", "corporacion", "especialidad", "despacho", "anio", "consecutivo", "recurso"))
