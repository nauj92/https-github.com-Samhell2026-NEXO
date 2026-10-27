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


def _v(valor, faltante):
    """Devuelve el valor o, si está vacío, un marcador entre corchetes para que el abogado lo complete."""
    valor = (str(valor).strip() if valor is not None else "")
    return valor if valor else f"[{faltante}]"


def _persona(nombre, tipo_doc, documento, domicilio, representante, rep_doc, etiqueta, desconocida=False, doc_opcional=False):
    if documento:
        doc = f"identificado(a) con {tipo_doc} {documento}".replace("  ", " ")
    elif doc_opcional:
        doc = "cuyo número de identificación no se conoce"
    else:
        doc = "identificado(a) con [número de identificación]"
    if desconocida:
        domicilio_txt = "de domicilio desconocido"
    else:
        domicilio_txt = f"domiciliado(a) en {_v(domicilio, 'domicilio')}"
    linea = f"{etiqueta}: {nombre}, {doc}, {domicilio_txt}."
    if representante:
        rd = f", identificado(a) con {rep_doc}" if rep_doc else ""
        linea += f" Actúa por medio de su representante legal {representante}{rd}."
    return linea


def borrador_demanda(d):
    """Borrador ordenado según los numerales del artículo 82 del Código General del Proceso."""
    juez = d.juez_destinatario or (d.juzgado.nombre if d.juzgado else "")
    ciudad = d.juzgado.ciudad if d.juzgado and d.juzgado.ciudad else ""
    destino = _v(juez, "JUEZ O JUZGADO COMPETENTE").upper()
    abogado = d.apoderado_nombre or (
        (d.abogado_responsable.get_full_name() or d.abogado_responsable.username) if d.abogado_responsable else ""
    )
    cliente = d.cliente.nombre if d.cliente else d.demandante

    partes = [
        _persona(d.demandante, d.demandante_tipo_documento, d.demandante_documento, d.demandante_domicilio,
                 d.demandante_representante, d.demandante_representante_documento, "DEMANDANTE"),
        _persona(d.demandado, d.demandado_tipo_documento, d.demandado_documento, d.demandado_domicilio,
                 d.demandado_representante, "", "DEMANDADO", desconocida=d.demandado_ubicacion_desconocida, doc_opcional=True),
    ]
    if d.otras_partes.strip():
        partes.append("OTRAS PARTES:\n" + d.otras_partes.strip())

    if d.sin_apoderado:
        apoderado = "El demandante actúa en nombre propio, sin apoderado judicial."
        presentacion = f"{d.demandante}, actuando en nombre propio,"
    else:
        tp = _v(d.apoderado_tarjeta_profesional, "T.P.")
        apoderado = (
            f"APODERADO DEL DEMANDANTE: {_v(abogado, 'nombre del apoderado')}, "
            f"identificado(a) con C.C. {_v(d.apoderado_documento, 'número')} y T.P. {tp}, "
            f"según poder que se anexa."
        )
        presentacion = f"{_v(abogado, 'nombre del apoderado')}, abogado(a) en ejercicio, obrando como apoderado(a) de {cliente},"

    hechos = [h for h in (d.hechos or []) if str(h).strip()]
    hechos_txt = "\n".join(f"{n}. {h}" for n, h in enumerate(hechos, 1)) if hechos else "1. [Hecho primero.]\n2. [Hecho segundo.]\n3. [Continuar numerando los hechos.]"

    pruebas = _v(d.pruebas, "Documentales, testimoniales, periciales y demás que se pretende hacer valer")
    if d.documentos_en_poder_demandado.strip():
        pruebas += "\n\nDocumentos que se encuentran en poder del demandado, para que los aporte:\n" + d.documentos_en_poder_demandado.strip()

    if d.requiere_juramento_estimatorio:
        juramento = _v(d.juramento_estimatorio, "Estimación razonada y bajo juramento de la suma pretendida, discriminando cada concepto")
    else:
        juramento = "No aplica en este proceso."

    if d.cuantia_aplica:
        cuantia = f"La cuantía del proceso se estima en {_pesos(d.cuantia)}."
    else:
        cuantia = "La estimación de la cuantía no es necesaria para determinar la competencia ni el trámite."

    def notif(etiqueta, direccion, email, desconocida=False):
        if desconocida:
            return f"{etiqueta}: se desconoce el lugar donde recibirá notificaciones personales."
        return f"{etiqueta}: dirección física {_v(direccion, 'dirección')}; correo electrónico {_v(email, 'correo electrónico')}."

    notificaciones = [
        notif("Demandante", d.notif_demandante_direccion, d.notif_demandante_email),
        notif("Demandado", d.notif_demandado_direccion, d.notif_demandado_email, d.demandado_ubicacion_desconocida),
    ]
    if not d.sin_apoderado:
        notificaciones.append(notif("Apoderado del demandante", d.notif_apoderado_direccion, d.notif_apoderado_email))

    firma_nombre = _v(abogado if not d.sin_apoderado else d.demandante, "nombre")
    firma_doc = (
        f"C.C. {_v(d.apoderado_documento, 'número')} · T.P. {_v(d.apoderado_tarjeta_profesional, 'número')}"
        if not d.sin_apoderado
        else f"{d.demandante_tipo_documento or 'C.C.'} {_v(d.demandante_documento, 'número')}"
    )

    return f"""Señor(a)
{destino}
{ciudad or "[ciudad]"}
E. S. D.

REFERENCIA: {d.clase_proceso.upper()}
DEMANDANTE: {d.demandante}
DEMANDADO: {d.demandado}

{presentacion} presento ante su despacho DEMANDA de {d.clase_proceso} contra {d.demandado}, con fundamento en lo siguiente:

I. DESIGNACIÓN DE LAS PARTES Y DEL APODERADO (art. 82, numerales 2 y 3)
{chr(10).join(partes)}
{apoderado}

II. PRETENSIONES (numeral 4)
{d.pretensiones}

III. HECHOS (numeral 5)
{hechos_txt}

IV. PRUEBAS (numeral 6)
{pruebas}

V. JURAMENTO ESTIMATORIO (numeral 7)
{juramento}

VI. FUNDAMENTOS DE DERECHO (numeral 8)
{_v(d.fundamentos_derecho, "Normas sustanciales y procesales aplicables")}

VII. CUANTÍA Y COMPETENCIA (numeral 9)
{cuantia} [Fundamento de la competencia por factor territorial, objetivo y funcional.]

VIII. NOTIFICACIONES (numeral 10)
{chr(10).join(notificaciones)}

IX. REQUISITOS ADICIONALES Y ANEXOS (numeral 11)
{_v(d.otros_requisitos, "Conciliación prejudicial u otro requisito de procedibilidad, poder, pruebas documentales, certificado de existencia y representación, traslados")}

Atentamente,

{firma_nombre}
{firma_doc}

(Plantilla generada por el sistema. Verifique el cumplimiento del artículo 82 del Código General del Proceso y las normas especiales de su clase de proceso. Si la demanda se presenta como mensaje de datos, no requiere firma digital: basta que el suscriptor se identifique con su nombre y documento de identificación — parágrafo 2 del artículo 82.)
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
