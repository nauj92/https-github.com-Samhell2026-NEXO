"""Borradores de escritos a partir de los datos registrados.

Son PLANTILLAS BASE: dejan marcados entre corchetes los datos que faltan (hechos, pruebas, anexos,
domicilios) y deben ser revisadas y completadas por el abogado antes de presentarse.
"""
from django.utils import timezone


def _pesos(valor):
    try:
        return f"${int(valor):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "[cuantía]"


def _fecha(f):
    return f.strftime("%d/%m/%Y") if f else "[fecha]"


def borrador_demanda(d):
    juzgado = d.juzgado.nombre if d.juzgado else "[JUZGADO COMPETENTE]"
    ciudad = d.juzgado.ciudad if d.juzgado and d.juzgado.ciudad else "[ciudad]"
    abogado = (d.abogado_responsable.get_full_name() or d.abogado_responsable.username) if d.abogado_responsable else "[nombre del apoderado]"
    cliente = d.cliente.nombre if d.cliente else d.demandante
    return f"""Señor(a)
{juzgado.upper()}
{ciudad}
E. S. D.

REFERENCIA: {d.clase_proceso.upper()}
DEMANDANTE: {d.demandante}
DEMANDADO: {d.demandado}

{abogado}, mayor de edad, identificado(a) como aparece al pie de mi firma, abogado(a) titulado(a) y en ejercicio, obrando como apoderado(a) de {cliente}, según poder que se anexa, presento ante su despacho DEMANDA de {d.clase_proceso} contra {d.demandado}, con fundamento en lo siguiente:

I. DESIGNACIÓN DE LAS PARTES Y SUS REPRESENTANTES
[Identificación, domicilio y representante legal de demandante y demandado.]

II. PRETENSIONES
{d.pretensiones}

III. HECHOS
1. [Hecho primero.]
2. [Hecho segundo.]
3. [Continuar numerando los hechos.]

IV. FUNDAMENTOS DE DERECHO
[Normas sustanciales y procesales aplicables.]

V. PRUEBAS
[Documentales, testimoniales, periciales y demás que se aportan o solicitan.]

VI. CUANTÍA Y COMPETENCIA
La cuantía del proceso se estima en {_pesos(d.cuantia)}. [Fundamento de la competencia por factor territorial, objetivo y funcional.]

VII. REQUISITO DE PROCEDIBILIDAD
[Conciliación prejudicial u otro requisito, si aplica.]

VIII. ANEXOS
[Poder, pruebas documentales, certificado de existencia y representación, traslados.]

IX. NOTIFICACIONES
[Direcciones físicas y electrónicas del demandante, del demandado y del apoderado.]

Atentamente,

{abogado}
C.C. [número] · T.P. [número]

(Plantilla base generada por el sistema: verifique que cumpla los requisitos del artículo 82 del Código General del Proceso y las normas especiales de su clase de proceso.)
"""


def borrador_contestacion(c):
    juzgado = c.juzgado.nombre if c.juzgado else "[JUZGADO]"
    ciudad = c.juzgado.ciudad if c.juzgado and c.juzgado.ciudad else "[ciudad]"
    radicado = c.expediente.numero if c.expediente else "[radicado]"
    abogado = (c.abogado_responsable.get_full_name() or c.abogado_responsable.username) if c.abogado_responsable else "[nombre del apoderado]"
    return f"""Señor(a)
{juzgado.upper()}
{ciudad}
E. S. D.

REFERENCIA: {c.clase_proceso.upper()}
RADICADO: {radicado}
DEMANDANTE: {c.demandante}
DEMANDADO: {c.demandado}
ASUNTO: CONTESTACIÓN DE LA DEMANDA

{abogado}, abogado(a) titulado(a) y en ejercicio, obrando como apoderado(a) de {c.demandado}, según poder que se anexa, dentro del término legal (notificación: {_fecha(c.fecha_notificacion)}; traslado de {c.dias_termino} días hábiles), contesto la demanda en los siguientes términos:

I. PRONUNCIAMIENTO SOBRE LOS HECHOS
1. Al hecho primero: [es cierto / no es cierto / no me consta].
2. Al hecho segundo: [...]

II. PRONUNCIAMIENTO SOBRE LAS PRETENSIONES
Me opongo a las pretensiones de la demanda por las razones que expongo a continuación. [Indicar cada pretensión y su posición.]

III. EXCEPCIONES
{c.excepciones or "[Excepciones de mérito y, si aplican, previas, cada una con su fundamento.]"}

IV. PRUEBAS
{c.pruebas or "[Documentales, testimoniales, periciales y demás que se aportan o solicitan.]"}

V. ANEXOS
[Poder, pruebas documentales, copias.]

VI. NOTIFICACIONES
[Direcciones físicas y electrónicas del demandado y del apoderado.]

Atentamente,

{abogado}
C.C. [número] · T.P. [número]

(Plantilla base generada el {timezone.localdate():%d/%m/%Y}: revise el cumplimiento del artículo 96 del Código General del Proceso y los requisitos de su clase de proceso.)
"""
