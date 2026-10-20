"""Cálculo de términos en días hábiles para Colombia.

Un día hábil es un día de lunes a viernes que no sea festivo. Los festivos se
calculan según la Ley 51 de 1983 (Ley Emiliani): los festivos "movibles" pasan
al lunes siguiente, y los religiosos dependen de la fecha de Pascua.

Convención de conteo: el día 1 del término es el primer día hábil POSTERIOR a
la fecha de inicio (la fecha de inicio no cuenta).

LIMITACIÓN: no considera la vacancia judicial (p. ej. 20 de diciembre a 10 de
enero), ni suspensiones de términos decretadas por el Consejo Superior de la
Judicatura, ni reglas especiales de cada jurisdicción. Es una ayuda de
cálculo; el vencimiento oficial debe confirmarlo el abogado responsable.
"""
from datetime import date, timedelta
from functools import lru_cache

from dateutil.easter import easter

ADVERTENCIA = (
    "Cálculo en días hábiles (lunes a viernes, sin festivos). No considera "
    "vacancia judicial ni suspensiones de términos: confirme el vencimiento."
)


def _siguiente_lunes(d):
    """Si la fecha no cae en lunes, la traslada al lunes siguiente (Ley Emiliani)."""
    return d if d.weekday() == 0 else d + timedelta(days=7 - d.weekday())


@lru_cache(maxsize=64)
def festivos(anio):
    """Devuelve {fecha: nombre} con los festivos de Colombia del año dado."""
    f = {}
    # Festivos fijos
    for mes, dia, nombre in [
        (1, 1, "Año Nuevo"),
        (5, 1, "Día del Trabajo"),
        (7, 20, "Día de la Independencia"),
        (8, 7, "Batalla de Boyacá"),
        (12, 8, "Inmaculada Concepción"),
        (12, 25, "Navidad"),
    ]:
        f[date(anio, mes, dia)] = nombre
    # Festivos trasladados al lunes (Ley Emiliani)
    for mes, dia, nombre in [
        (1, 6, "Día de los Reyes Magos"),
        (3, 19, "Día de San José"),
        (6, 29, "San Pedro y San Pablo"),
        (8, 15, "Asunción de la Virgen"),
        (10, 12, "Día de la Raza"),
        (11, 1, "Día de Todos los Santos"),
        (11, 11, "Independencia de Cartagena"),
    ]:
        f[_siguiente_lunes(date(anio, mes, dia))] = nombre
    # Festivos que dependen de la Pascua
    pascua = easter(anio)
    f[pascua - timedelta(days=3)] = "Jueves Santo"
    f[pascua - timedelta(days=2)] = "Viernes Santo"
    f[_siguiente_lunes(pascua + timedelta(days=39))] = "Ascensión del Señor"
    f[_siguiente_lunes(pascua + timedelta(days=60))] = "Corpus Christi"
    f[_siguiente_lunes(pascua + timedelta(days=68))] = "Sagrado Corazón de Jesús"
    return f


def es_dia_habil(d):
    return d.weekday() < 5 and d not in festivos(d.year)


def sumar_dias_habiles(inicio, dias):
    """Fecha en que vence un término de `dias` días hábiles contados desde `inicio`."""
    if dias < 0:
        raise ValueError("Los días deben ser un número positivo.")
    actual = inicio
    restantes = dias
    while restantes > 0:
        actual += timedelta(days=1)
        if es_dia_habil(actual):
            restantes -= 1
    return actual


def festivos_en_rango(desde, hasta):
    """Lista de (fecha, nombre) de festivos entre dos fechas, ambas incluidas."""
    resultado = []
    for anio in range(desde.year, hasta.year + 1):
        for fecha, nombre in festivos(anio).items():
            if desde <= fecha <= hasta:
                resultado.append((fecha, nombre))
    return sorted(resultado)
