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
