"""Verificación de los requisitos de la demanda del artículo 82 del Código General del Proceso.

Es una ayuda de revisión: indica qué numerales están diligenciados y cuáles faltan. No reemplaza el criterio
del abogado ni los requisitos especiales de cada clase de proceso.
"""

NUMERALES = {
    1: "Designación del juez a quien se dirige",
    2: "Nombre, domicilio e identificación de las partes y sus representantes",
    3: "Apoderado judicial del demandante",
    4: "Lo que se pretende, con precisión y claridad",
    5: "Hechos determinados, clasificados y numerados",
    6: "Petición de pruebas",
    7: "Juramento estimatorio",
    8: "Fundamentos de derecho",
    9: "Cuantía del proceso",
    10: "Lugar y direcciones para notificaciones",
    11: "Los demás que exija la ley",
}


def _lleno(valor):
    return bool(str(valor or "").strip())


def _hechos_validos(d):
    return [h for h in (d.hechos or []) if _lleno(h)]


def requisitos_art82(d):
    """Devuelve la lista de numerales con `cumple` (True/False/None si es solo informativo) y lo que falta."""
    items = []

    def agregar(numeral, faltas, informativo=False):
        items.append(
            {
                "numeral": numeral,
                "titulo": NUMERALES[numeral],
                "cumple": None if informativo else not faltas,
                "falta": faltas,
            }
        )

    # 1. Juez
    agregar(1, [] if (_lleno(d.juez_destinatario) or d.juzgado_id) else ["Indique el juez o juzgado al que se dirige la demanda."])

    # 2. Partes
    f = []
    if not _lleno(d.demandante):
        f.append("Falta el nombre del demandante.")
    if not _lleno(d.demandante_documento):
        f.append("Falta el número de identificación del demandante (NIT si es persona jurídica).")
    if not _lleno(d.demandante_domicilio):
        f.append("Falta el domicilio del demandante.")
    if d.demandante_tipo_persona == "juridica" and not _lleno(d.demandante_representante):
        f.append("El demandante es persona jurídica: indique su representante legal.")
    if not _lleno(d.demandado):
        f.append("Falta el nombre del demandado.")
    if not d.demandado_ubicacion_desconocida:
        if not _lleno(d.demandado_domicilio):
            f.append("Falta el domicilio del demandado (o marque que se desconoce).")
        if d.demandado_tipo_persona == "juridica" and not _lleno(d.demandado_representante):
            f.append("El demandado es persona jurídica: indique su representante legal.")
    agregar(2, f)

    # 3. Apoderado
    f = []
    if not d.sin_apoderado:
        if not _lleno(d.apoderado_nombre):
            f.append("Falta el nombre del apoderado (o marque que actúa sin apoderado).")
        if not _lleno(d.apoderado_documento):
            f.append("Falta la identificación del apoderado.")
        if not _lleno(d.apoderado_tarjeta_profesional):
            f.append("Falta la tarjeta profesional del apoderado.")
    agregar(3, f)

    # 4. Pretensiones
    agregar(4, [] if len((d.pretensiones or "").strip()) >= 10 else ["Describa las pretensiones."])

    # 5. Hechos
    agregar(5, [] if _hechos_validos(d) else ["Agregue al menos un hecho."])

    # 6. Pruebas
    agregar(6, [] if _lleno(d.pruebas) else ["Indique las pruebas que se pretende hacer valer."])

    # 7. Juramento estimatorio (solo cuando es necesario)
    f = []
    if d.requiere_juramento_estimatorio and not _lleno(d.juramento_estimatorio):
        f.append("Redacte el juramento estimatorio (o desmarque que sea necesario).")
    agregar(7, f)

    # 8. Fundamentos de derecho
    agregar(8, [] if _lleno(d.fundamentos_derecho) else ["Indique los fundamentos de derecho."])

    # 9. Cuantía (solo cuando es necesaria)
    f = []
    if d.cuantia_aplica and not (d.cuantia and d.cuantia > 0):
        f.append("Indique la cuantía (o desmarque que sea necesaria para la competencia o el trámite).")
    agregar(9, f)

    # 10. Notificaciones
    f = []
    if not (_lleno(d.notif_demandante_direccion) or _lleno(d.notif_demandante_email)):
        f.append("Falta la dirección física o electrónica del demandante para notificaciones.")
    if not d.sin_apoderado and not (_lleno(d.notif_apoderado_direccion) or _lleno(d.notif_apoderado_email)):
        f.append("Falta la dirección física o electrónica del apoderado para notificaciones.")
    if not d.demandado_ubicacion_desconocida and not (_lleno(d.notif_demandado_direccion) or _lleno(d.notif_demandado_email)):
        f.append("Falta el lugar de notificación del demandado (o marque que se desconoce).")
    agregar(10, f)

    # 11. Informativo
    agregar(11, [], informativo=True)

    evaluables = [i for i in items if i["cumple"] is not None]
    return {
        "total": len(evaluables),
        "cumplidos": sum(1 for i in evaluables if i["cumple"]),
        "items": items,
    }


# ---------------------------------------------------------------------------
# Artículo 96 CGP: contestación de la demanda
# ---------------------------------------------------------------------------
NUMERALES_ART96 = {
    1: "Nombre, domicilio e identificación del demandado y de su representante o apoderado",
    2: "Pronunciamiento expreso sobre las pretensiones y los hechos",
    3: "Excepciones de mérito, juramento estimatorio y derecho de retención",
    4: "Petición de pruebas",
    5: "Lugar y direcciones para notificaciones",
    6: "Anexos de la contestación",
}

RESPUESTAS_HECHO = ("admite", "niega", "no_consta")
MIN_RAZONES = 10


def requisitos_art96(c):
    """Numerales del artículo 96 CGP con `cumple` (True/False) y lo que falta en cada uno."""
    items = []

    def agregar(numeral, faltas):
        items.append({"numeral": numeral, "titulo": NUMERALES_ART96[numeral], "cumple": not faltas, "falta": faltas})

    # 1. Demandado y apoderado
    f = []
    if not _lleno(c.demandado):
        f.append("Falta el nombre del demandado.")
    if not _lleno(c.demandado_documento):
        f.append("Falta el número de identificación del demandado (NIT si es persona jurídica).")
    if not _lleno(c.demandado_domicilio):
        f.append("Falta el domicilio del demandado.")
    if c.demandado_tipo_persona == "juridica":
        if not _lleno(c.demandado_representante):
            f.append("El demandado es persona jurídica: indique su representante legal.")
        if not _lleno(c.demandado_representante_documento):
            f.append("Falta el documento de identificación del representante legal.")
    if not c.sin_apoderado:
        if not _lleno(c.apoderado_nombre):
            f.append("Falta el nombre del apoderado (o marque que el demandado comparece por sí mismo).")
        if not _lleno(c.apoderado_documento):
            f.append("Falta la identificación del apoderado.")
        if not _lleno(c.apoderado_tarjeta_profesional):
            f.append("Falta la tarjeta profesional del apoderado.")
        if not _lleno(c.apoderado_domicilio):
            f.append("Falta el domicilio del apoderado.")
    agregar(1, f)

    # 2. Pronunciamiento sobre pretensiones y hechos
    f = []
    if not _lleno(c.pronunciamiento_pretensiones):
        f.append("Falta el pronunciamiento expreso y concreto sobre las pretensiones.")
    hechos = [h for h in (c.pronunciamientos_hechos or []) if isinstance(h, dict) and _lleno(h.get("hecho"))]
    if not hechos:
        f.append("Pronúnciese sobre cada hecho de la demanda: agréguelos uno por uno.")
    for i, h in enumerate(hechos, start=1):
        respuesta = h.get("respuesta")
        if respuesta not in RESPUESTAS_HECHO:
            f.append(f"Hecho {i}: indique si se admite, se niega o no le consta.")
        elif respuesta != "admite" and len((h.get("razones") or "").strip()) < MIN_RAZONES:
            f.append(f"Hecho {i}: explique de forma precisa y unívoca las razones; de lo contrario se presumirá cierto.")
    agregar(2, f)

    # 3. Excepciones de mérito, juramento estimatorio, derecho de retención
    f = []
    excepciones = [e for e in (c.excepciones_merito or []) if isinstance(e, dict) and (_lleno(e.get("nombre")) or _lleno(e.get("fundamento")))]
    if not c.sin_excepciones:
        if not excepciones:
            f.append("Proponga al menos una excepción de mérito o marque que no se propone ninguna.")
        for i, e in enumerate(excepciones, start=1):
            if not _lleno(e.get("nombre")):
                f.append(f"Excepción {i}: falta el nombre.")
            if not _lleno(e.get("fundamento")):
                f.append(f"Excepción {i}: falta su fundamento fáctico.")
    if c.objeta_juramento_estimatorio and not _lleno(c.objecion_juramento):
        f.append("Redacte la objeción al juramento estimatorio (o desmarque la casilla).")
    if c.alega_derecho_retencion and not _lleno(c.derecho_retencion):
        f.append("Explique el derecho de retención que alega (o desmarque la casilla).")
    agregar(3, f)

    # 4. Pruebas
    agregar(4, [] if (c.pruebas_en_expediente or _lleno(c.pruebas)) else
            ["Indique las pruebas que pretende hacer valer (o marque que ya obran en el expediente)."])

    # 5. Notificaciones
    f = []
    if not (_lleno(c.notif_demandado_direccion) or _lleno(c.notif_demandado_email)):
        f.append("Falta la dirección física o electrónica del demandado para notificaciones.")
    if not c.sin_apoderado and not (_lleno(c.notif_apoderado_direccion) or _lleno(c.notif_apoderado_email)):
        f.append("Falta la dirección física o electrónica del apoderado para notificaciones.")
    agregar(5, f)

    # Anexos
    f = []
    if not c.sin_apoderado and not c.anexo_poder:
        f.append("Se debe acompañar el poder de quien suscribe la contestación (marque cuando lo anexe).")
    if c.demandado_tipo_persona == "juridica" and not c.anexo_existencia_representacion:
        f.append("Se debe acompañar la prueba de existencia y representación del demandado (marque cuando la anexe).")
    agregar(6, f)

    return {"total": len(items), "cumplidos": sum(1 for i in items if i["cumple"]), "items": items}
