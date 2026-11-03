"""Cálculo de términos en días hábiles para Colombia.

Un día hábil es un día de lunes a viernes que no sea festivo. Los festivos se
calculan según la Ley 51 de 1983 (Ley Emiliani): los festivos "movibles" pasan
al lunes siguiente, y los religiosos dependen de la fecha de Pascua.

Convención de conteo: el día 1 del término es el primer día hábil POSTERIOR a
la fecha de inicio (la fecha de inicio no cuenta).

Vacancia judicial (opcional): la Rama Judicial tiene vacancia colectiva en
Semana Santa y del 20 de diciembre al 10 de enero (art. 146 de la Ley 270 de
1996). Con `vacancia=True` esos días tampoco cuentan como hábiles. Se activa
por llamada o para todo el sistema con la variable PLAZOS_CON_VACANCIA.

LIMITACIÓN: no considera suspensiones de términos decretadas por el Consejo
Superior de la Judicatura, ni reglas especiales de cada jurisdicción (por
ejemplo, la tutela y varias actuaciones penales y de familia no se suspenden
en vacancia). Es una ayuda de cálculo; el vencimiento oficial debe
confirmarlo el abogado responsable.
"""
from datetime import date, timedelta
from functools import lru_cache

from dateutil.easter import easter

ADVERTENCIA = (
    "Cálculo en días hábiles (lunes a viernes, sin festivos). No considera "
    "vacancia judicial ni suspensiones de términos: confirme el vencimiento."
)
ADVERTENCIA_VACANCIA = (
    "Cálculo en días hábiles (lunes a viernes, sin festivos) descontando la vacancia judicial "
    "(Semana Santa y del 20 de diciembre al 10 de enero). No considera suspensiones de términos "
    "ni las actuaciones que no se suspenden en vacancia: confirme el vencimiento."
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


def semana_santa(anio):
    """(lunes, viernes) de la Semana Santa del año: periodo de vacancia judicial."""
    pascua = easter(anio)
    return pascua - timedelta(days=6), pascua - timedelta(days=2)


def es_vacancia_judicial(d):
    """True si la fecha cae en vacancia judicial colectiva (Semana Santa o 20 de diciembre a 10 de enero)."""
    if (d.month == 12 and d.day >= 20) or (d.month == 1 and d.day <= 10):
        return True
    lunes, viernes = semana_santa(d.year)
    return lunes <= d <= viernes


def _con_vacancia(vacancia):
    """None = usar la configuración del sistema (PLAZOS_CON_VACANCIA, por defecto apagada)."""
    if vacancia is not None:
        return vacancia
    try:
        from django.conf import settings

        return bool(getattr(settings, "PLAZOS_CON_VACANCIA", False))
    except Exception:
        return False


def es_dia_habil(d, vacancia=False):
    if d.weekday() >= 5 or d in festivos(d.year):
        return False
    return not (vacancia and es_vacancia_judicial(d))


def sumar_dias_habiles(inicio, dias, vacancia=None):
    """Fecha en que vence un término de `dias` días hábiles contados desde `inicio`.

    `vacancia`: True descuenta la vacancia judicial; False no; None usa la configuración del sistema.
    """
    if dias < 0:
        raise ValueError("Los días deben ser un número positivo.")
    vacancia = _con_vacancia(vacancia)
    actual = inicio
    restantes = dias
    while restantes > 0:
        actual += timedelta(days=1)
        if es_dia_habil(actual, vacancia):
            restantes -= 1
    return actual


def dias_de_vacancia_en_rango(desde, hasta):
    """Cantidad de días de lunes a viernes no festivos que cayeron en vacancia judicial entre dos fechas."""
    total = 0
    d = desde
    while d <= hasta:
        if es_dia_habil(d) and es_vacancia_judicial(d):
            total += 1
        d += timedelta(days=1)
    return total


def festivos_en_rango(desde, hasta):
    """Lista de (fecha, nombre) de festivos entre dos fechas, ambas incluidas."""
    resultado = []
    for anio in range(desde.year, hasta.year + 1):
        for fecha, nombre in festivos(anio).items():
            if desde <= fecha <= hasta:
                resultado.append((fecha, nombre))
    return sorted(resultado)
