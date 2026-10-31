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


_RESPUESTA_TXT = {"admite": "SE ADMITE", "niega": "NO ES CIERTO", "no_consta": "NO ME CONSTA"}


def borrador_contestacion(c):
    """Borrador ordenado según el artículo 96 del Código General del Proceso."""
    juzgado = c.juzgado.nombre if c.juzgado else "[JUZGADO]"
    ciudad = c.juzgado.ciudad if c.juzgado and c.juzgado.ciudad else "[ciudad]"
    radicado = c.expediente.numero if c.expediente else "[radicado]"
    abogado = c.apoderado_nombre or (
        (c.abogado_responsable.get_full_name() or c.abogado_responsable.username) if c.abogado_responsable else ""
    )

    # 1. Demandado y apoderado
    persona = _persona(
        c.demandado, c.demandado_tipo_documento, c.demandado_documento, c.demandado_domicilio,
        c.demandado_representante, c.demandado_representante_documento, "DEMANDADO",
    )
    if c.sin_apoderado:
        apoderado_txt = "El demandado comparece por sí mismo, sin apoderado judicial."
        presentacion = f"{c.demandado}, actuando en nombre propio,"
        firma, firma_doc = c.demandado, _v(c.demandado_documento, "identificación")
    else:
        apoderado_txt = (
            f"APODERADO: {_v(abogado, 'nombre del apoderado')}, identificado(a) con C.C. {_v(c.apoderado_documento, 'número')} "
            f"y T.P. {_v(c.apoderado_tarjeta_profesional, 'T.P.')}, domiciliado(a) en {_v(c.apoderado_domicilio, 'domicilio')}."
        )
        presentacion = f"{_v(abogado, 'nombre del apoderado')}, abogado(a) en ejercicio, obrando como apoderado(a) de {c.demandado},"
        firma = _v(abogado, "nombre del apoderado")
        firma_doc = f"C.C. {_v(c.apoderado_documento, 'número')} · T.P. {_v(c.apoderado_tarjeta_profesional, 'número')}"

    # 2. Pronunciamiento
    hechos = [h for h in (c.pronunciamientos_hechos or []) if isinstance(h, dict) and str(h.get("hecho", "")).strip()]
    if hechos:
        bloques = []
        for i, h in enumerate(hechos, start=1):
            resp = _RESPUESTA_TXT.get(h.get("respuesta"), "[admite / niega / no le consta]")
            linea = f"AL HECHO {i}: {resp}."
            razones = str(h.get("razones") or "").strip()
            if h.get("respuesta") in ("niega", "no_consta"):
                linea += f" {razones}" if razones else " [Exprese de forma precisa y unívoca las razones; si no lo hace, el hecho se presumirá cierto.]"
            bloques.append(f"{linea}\n   (Hecho de la demanda: {h['hecho']})")
        hechos_txt = "\n".join(bloques)
    else:
        hechos_txt = "[Pronúnciese sobre cada hecho de la demanda indicando los que admite, los que niega y los que no le constan, con sus razones.]"
    pretensiones = _v(c.pronunciamiento_pretensiones, "Pronunciamiento expreso y concreto sobre cada pretensión")

    # 3. Excepciones, juramento estimatorio, derecho de retención
    excepciones = [e for e in (c.excepciones_merito or []) if isinstance(e, dict) and str(e.get("nombre", "")).strip()]
    if excepciones:
        exc_txt = "\n".join(
            f"{i}. {e['nombre'].upper()}\n   {_v(e.get('fundamento'), 'Fundamento fáctico')}" for i, e in enumerate(excepciones, start=1)
        )
    elif c.sin_excepciones:
        exc_txt = "No se proponen excepciones de mérito."
    else:
        exc_txt = "[Excepciones de mérito, cada una con su fundamento fáctico.]"
    if c.excepciones.strip():
        exc_txt += "\n\nOtras excepciones o consideraciones:\n" + c.excepciones.strip()
    juramento = (
        _v(c.objecion_juramento, "Objeción al juramento estimatorio, razonada y especificando la inexactitud que se le atribuye")
        if c.objeta_juramento_estimatorio else "No se formula objeción al juramento estimatorio."
    )
    retencion = (
        _v(c.derecho_retencion, "Derecho de retención que se alega y su fundamento")
        if c.alega_derecho_retencion else "No se alega derecho de retención."
    )

    # 4. Pruebas
    pruebas = c.pruebas.strip() or ("Las pruebas que se pretende hacer valer ya obran en el expediente." if c.pruebas_en_expediente else "[Pruebas que se pretende hacer valer]")
    if c.pruebas_en_expediente and c.pruebas.strip():
        pruebas += "\nAdicionalmente, se solicita tener como prueba las que ya obran en el expediente."

    # 5. Notificaciones
    notif = [f"El demandado: {_v(c.notif_demandado_direccion, 'dirección física')}; correo electrónico: {_v(c.notif_demandado_email, 'correo electrónico')}."]
    if not c.sin_apoderado:
        notif.append(f"El apoderado: {_v(c.notif_apoderado_direccion, 'dirección física')}; correo electrónico: {_v(c.notif_apoderado_email, 'correo electrónico')}.")

    # Anexos
    anexos = []
    if not c.sin_apoderado:
        anexos.append("Poder conferido para actuar en nombre del demandado.")
    if c.demandado_tipo_persona == "juridica":
        anexos.append("Certificado de existencia y representación legal del demandado.")
    docs = c.documentos_solicitados.strip()
    anexos.append(f"Documentos en poder del demandado solicitados por el demandante: {docs}" if docs else
                  "Documentos solicitados por el demandante: [se aportan / manifiesto que el demandado no los tiene].")
    anexos.append("Las pruebas documentales que se pretende hacer valer.")
    if c.anexos_otros.strip():
        anexos.append(c.anexos_otros.strip())
    anexos_txt = "\n".join(f"{i}. {a}" for i, a in enumerate(anexos, start=1))

    return f"""Señor(a)
{juzgado.upper()}
{ciudad}
E. S. D.

REFERENCIA: {c.clase_proceso.upper()}
RADICADO: {radicado}
DEMANDANTE: {c.demandante}
DEMANDADO: {c.demandado}
ASUNTO: CONTESTACIÓN DE LA DEMANDA

{presentacion} dentro del término legal (notificación: {_fecha(c.fecha_notificacion)}; traslado de {c.dias_termino} días hábiles), contesto la demanda en los siguientes términos:

I. IDENTIFICACIÓN DEL DEMANDADO Y DE SU APODERADO (art. 96, numeral 1)
{persona}
{apoderado_txt}

II. PRONUNCIAMIENTO SOBRE LOS HECHOS Y LAS PRETENSIONES (numeral 2)
A. Hechos
{hechos_txt}

B. Pretensiones
{pretensiones}

III. EXCEPCIONES DE MÉRITO (numeral 3)
{exc_txt}

Juramento estimatorio: {juramento}
Derecho de retención: {retencion}

IV. PRUEBAS (numeral 4)
{pruebas}

V. NOTIFICACIONES (numeral 5)
{chr(10).join(notif)}

VI. ANEXOS
{anexos_txt}

Atentamente,

{firma}
{firma_doc}

(Plantilla generada el {timezone.localdate():%d/%m/%Y}: revise el cumplimiento del artículo 96 del Código General del Proceso y los requisitos de su clase de proceso. Recuerde que, si no se pronuncia de forma precisa y unívoca sobre los hechos que niega o que no le constan, se presumirán ciertos.)
"""
