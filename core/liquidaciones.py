"""Cálculos de liquidación: laboral, de crédito (capital + intereses de mora) y de cuotas de administración.

Son funciones puras (sin base de datos) para poder probarlas con facilidad. Todos los valores
monetarios del resultado son pesos enteros (redondeo al peso) y las fechas van en ISO (AAAA-MM-DD).

IMPORTANTE: son herramientas de apoyo. Las tasas (interés bancario corriente, usura), el salario
mínimo y el auxilio de transporte DEBEN digitarse según la certificación vigente para el período;
el sistema no los trae de ninguna fuente. El abogado responsable debe verificar el resultado.
"""
import calendar
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

ADVERTENCIA = (
    "Cálculo de apoyo. Verifique tasas, salario mínimo y fechas con la certificación vigente "
    "y revise el resultado antes de presentarlo."
)


class ErrorLiquidacion(ValueError):
    """Dato inconsistente para liquidar; el mensaje va dirigido al usuario."""


def _d(valor):
    return Decimal(str(valor))


def pesos(valor):
    """Redondea al peso (mitad hacia arriba) y devuelve un entero."""
    return int(_d(valor).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _iso(f):
    return f.isoformat() if f else None


def tasa_mensual(ea_porcentaje):
    """Tasa mensual equivalente a una tasa efectiva anual: (1 + EA)^(1/12) - 1 (como fracción)."""
    ea = _d(ea_porcentaje) / Decimal(100)
    return (Decimal(1) + ea) ** (Decimal(1) / Decimal(12)) - Decimal(1)


def dias_360(inicio, fin):
    """Días entre dos fechas, ambas incluidas, con año comercial de 360 días (meses de 30).

    Convención laboral: el último día de febrero cuenta como día 30.
    """
    if fin < inicio:
        return 0

    def dia(f):
        if f.month == 2 and f.day == calendar.monthrange(f.year, 2)[1]:
            return 30
        return min(f.day, 30)

    return (fin.year - inicio.year) * 360 + (fin.month - inicio.month) * 30 + (dia(fin) - dia(inicio)) + 1


# --------------------------------------------------------------------------------------------
# Liquidación laboral
# --------------------------------------------------------------------------------------------
def liquidar_laboral(
    salario_mensual,
    fecha_inicio,
    fecha_fin,
    auxilio_transporte=0,
    desde_cesantias=None,
    desde_prima=None,
    desde_vacaciones=None,
    dias_vacaciones_disfrutados=0,
    salarios_pendientes_dias=0,
    deducciones=0,
    indemnizacion=False,
    tipo_contrato="indefinido",
    fecha_fin_pactada=None,
    salario_minimo=None,
):
    salario = _d(salario_mensual)
    auxilio = _d(auxilio_transporte or 0)
    if salario <= 0:
        raise ErrorLiquidacion("El salario debe ser mayor que cero.")
    if fecha_fin < fecha_inicio:
        raise ErrorLiquidacion("La fecha de terminación no puede ser anterior a la de inicio.")

    # Períodos por defecto: cesantías e intereses desde el 1 de enero del año de retiro; prima desde el
    # inicio del semestre de retiro; vacaciones desde el inicio del contrato.
    inicio_anio = date(fecha_fin.year, 1, 1)
    inicio_semestre = date(fecha_fin.year, 1 if fecha_fin.month <= 6 else 7, 1)
    d_ces = max(desde_cesantias or inicio_anio, fecha_inicio)
    d_pri = max(desde_prima or inicio_semestre, fecha_inicio)
    d_vac = max(desde_vacaciones or fecha_inicio, fecha_inicio)
    for nombre, f in (("cesantías", d_ces), ("prima", d_pri), ("vacaciones", d_vac)):
        if f > fecha_fin:
            raise ErrorLiquidacion(f"La fecha desde la que se liquidan las {nombre} es posterior a la terminación.")

    base_prestaciones = salario + auxilio
    dias_c = dias_360(d_ces, fecha_fin)
    dias_p = dias_360(d_pri, fecha_fin)
    dias_v = dias_360(d_vac, fecha_fin)
    dias_totales = dias_360(fecha_inicio, fecha_fin)

    conceptos = []

    def agregar(nombre, formula, dias, valor):
        conceptos.append({"concepto": nombre, "formula": formula, "dias": dias, "valor": pesos(valor)})

    if salarios_pendientes_dias:
        agregar(
            "Salarios pendientes",
            f"Salario / 30 × {salarios_pendientes_dias} días",
            salarios_pendientes_dias,
            salario / 30 * salarios_pendientes_dias,
        )

    cesantias = base_prestaciones * dias_c / 360
    agregar("Cesantías", "(Salario + auxilio) × días / 360", dias_c, cesantias)
    agregar("Intereses sobre cesantías", "Cesantías × días × 12% / 360", dias_c, cesantias * dias_c * Decimal("0.12") / 360)
    agregar("Prima de servicios", "(Salario + auxilio) × días / 360", dias_p, base_prestaciones * dias_p / 360)

    dias_pago_vac = salario * dias_v / 720
    descuento_vac = salario / 30 * dias_vacaciones_disfrutados
    vacaciones = max(Decimal(0), dias_pago_vac - descuento_vac)
    agregar(
        "Vacaciones",
        f"Salario × días / 720, menos {dias_vacaciones_disfrutados} día(s) hábiles ya disfrutados",
        dias_v,
        vacaciones,
    )

    supuestos = [
        f"Cesantías e intereses liquidados desde {_iso(d_ces)} (por defecto, 1 de enero del año de retiro).",
        f"Prima liquidada desde {_iso(d_pri)} (por defecto, inicio del semestre de retiro).",
        f"Vacaciones liquidadas desde {_iso(d_vac)} (por defecto, inicio del contrato).",
        "Se usa el año comercial de 360 días. El auxilio de transporte entra a la base de cesantías y prima, no a la de vacaciones.",
    ]

    if indemnizacion:
        if tipo_contrato == "fijo":
            if not fecha_fin_pactada or fecha_fin_pactada <= fecha_fin:
                raise ErrorLiquidacion("Para contrato a término fijo indique una fecha de terminación pactada posterior al retiro.")
            restantes = (fecha_fin_pactada - fecha_fin).days
            agregar(
                "Indemnización por despido sin justa causa (término fijo)",
                f"Salario / 30 × {restantes} días que faltaban del plazo (art. 64 CST)",
                restantes,
                salario / 30 * restantes,
            )
        else:
            if not salario_minimo or _d(salario_minimo) <= 0:
                raise ErrorLiquidacion("Para calcular la indemnización indique el salario mínimo vigente.")
            anios = Decimal(dias_totales) / Decimal(360)
            if salario < 10 * _d(salario_minimo):
                primer, siguiente = 30, 20
            else:
                primer, siguiente = 20, 15
            dias_indem = Decimal(primer) if anios <= 1 else Decimal(primer) + Decimal(siguiente) * (anios - 1)
            agregar(
                "Indemnización por despido sin justa causa (término indefinido)",
                f"Salario / 30 × {dias_indem.quantize(Decimal('0.01'))} días ({primer} por el primer año y {siguiente} por cada año adicional, proporcional; art. 64 CST)",
                float(dias_indem.quantize(Decimal("0.01"))),
                salario / 30 * dias_indem,
            )
        supuestos.append("La indemnización se calcula con el último salario, sin auxilio de transporte.")

    subtotal = sum(c["valor"] for c in conceptos)
    deducciones_p = pesos(deducciones or 0)
    return {
        "tipo": "laboral",
        "periodo": {"desde": _iso(fecha_inicio), "hasta": _iso(fecha_fin), "dias_360": dias_totales},
        "conceptos": conceptos,
        "subtotal": subtotal,
        "deducciones": deducciones_p,
        "total": subtotal - deducciones_p,
        "supuestos": supuestos,
        "advertencia": ADVERTENCIA + " No incluye la sanción moratoria (art. 65 CST), aportes ni retención.",
    }


# --------------------------------------------------------------------------------------------
# Liquidación de crédito (capital + intereses de mora)
# --------------------------------------------------------------------------------------------
def liquidar_credito(capital, fecha_inicio_mora, fecha_corte, tasa_ea=None, periodos=None, abonos=None, costas=0, otros=0):
    """Intereses de mora sobre un capital, con tasas por período y abonos.

    - Interés de un tramo = capital vigente × tasa mensual × días / 30, con
      tasa mensual = (1 + EA)^(1/12) - 1. La fecha de inicio de mora es el primer día que causa interés.
    - Los abonos se imputan primero a los intereses causados y luego al capital (art. 1653 C.C.).
    - `periodos`: lista de dicts {desde, hasta, tasa_ea}; deben cubrir todo el rango sin huecos.
      Si no se dan, se usa `tasa_ea` para todo el rango.
    """
    capital = _d(capital)
    if capital <= 0:
        raise ErrorLiquidacion("El capital debe ser mayor que cero.")
    if fecha_corte < fecha_inicio_mora:
        raise ErrorLiquidacion("La fecha de corte no puede ser anterior al inicio de la mora.")

    periodos = sorted(periodos or [], key=lambda p: p["desde"])
    if periodos:
        if periodos[0]["desde"] > fecha_inicio_mora:
            raise ErrorLiquidacion("Los períodos de tasas deben cubrir desde la fecha de inicio de la mora.")
        for ant, sig in zip(periodos, periodos[1:]):
            if sig["desde"] <= ant["hasta"]:
                raise ErrorLiquidacion("Los períodos de tasas no pueden superponerse.")
            if sig["desde"] != ant["hasta"] + timedelta(days=1):
                raise ErrorLiquidacion("Hay un hueco entre períodos de tasas: cada uno debe empezar el día siguiente al anterior.")
        for p in periodos:
            if p["hasta"] < p["desde"]:
                raise ErrorLiquidacion("Un período de tasa termina antes de empezar.")
        if periodos[-1]["hasta"] < fecha_corte:
            raise ErrorLiquidacion("Los períodos de tasas deben cubrir hasta la fecha de corte.")
    elif tasa_ea is None:
        raise ErrorLiquidacion("Indique la tasa de interés (efectiva anual) o los períodos de tasas.")

    def tasa_en(f):
        if not periodos:
            return _d(tasa_ea)
        for p in periodos:
            if p["desde"] <= f <= p["hasta"]:
                return _d(p["tasa_ea"])
        raise ErrorLiquidacion("No hay tasa definida para una de las fechas.")

    abonos = sorted(abonos or [], key=lambda a: a["fecha"])
    for a in abonos:
        if a["fecha"] < fecha_inicio_mora or a["fecha"] > fecha_corte:
            raise ErrorLiquidacion("Los abonos deben estar entre el inicio de la mora y la fecha de corte.")
        if _d(a["valor"]) <= 0:
            raise ErrorLiquidacion("El valor de cada abono debe ser mayor que cero.")

    cortes = {fecha_inicio_mora, fecha_corte + timedelta(days=1)}
    for p in periodos:
        if fecha_inicio_mora < p["desde"] <= fecha_corte:
            cortes.add(p["desde"])
    for a in abonos:
        cortes.add(a["fecha"] + timedelta(days=1))
    cortes = sorted(c for c in cortes if fecha_inicio_mora <= c <= fecha_corte + timedelta(days=1))

    capital_vivo = capital
    intereses_pend = Decimal(0)
    intereses_causados = Decimal(0)
    intereses_pagados = Decimal(0)
    tramos = []
    movimientos = []
    pendientes_abono = list(abonos)

    for inicio, siguiente in zip(cortes, cortes[1:]):
        fin = siguiente - timedelta(days=1)
        dias = (fin - inicio).days + 1
        ea = tasa_en(inicio)
        tm = tasa_mensual(ea)
        interes = capital_vivo * tm * dias / 30
        intereses_causados += interes
        intereses_pend += interes
        tramos.append(
            {
                "desde": _iso(inicio),
                "hasta": _iso(fin),
                "dias": dias,
                "tasa_ea": float(ea),
                "tasa_mensual": float((tm * 100).quantize(Decimal("0.0001"))),
                "capital": pesos(capital_vivo),
                "interes": pesos(interes),
            }
        )
        # abonos que ocurren al terminar este tramo
        while pendientes_abono and pendientes_abono[0]["fecha"] == fin:
            ab = pendientes_abono.pop(0)
            valor = _d(ab["valor"])
            a_intereses = min(valor, intereses_pend)
            a_capital = valor - a_intereses
            if a_capital > capital_vivo:
                raise ErrorLiquidacion(f"El abono del {ab['fecha']:%d/%m/%Y} supera la deuda a esa fecha.")
            intereses_pend -= a_intereses
            intereses_pagados += a_intereses
            capital_vivo -= a_capital
            movimientos.append(
                {
                    "fecha": _iso(ab["fecha"]),
                    "valor": pesos(valor),
                    "a_intereses": pesos(a_intereses),
                    "a_capital": pesos(a_capital),
                }
            )

    costas = _d(costas or 0)
    otros = _d(otros or 0)
    total = capital_vivo + intereses_pend + costas + otros
    return {
        "tipo": "credito",
        "tramos": tramos,
        "abonos": movimientos,
        "capital_inicial": pesos(capital),
        "capital_pendiente": pesos(capital_vivo),
        "intereses_causados": pesos(intereses_causados),
        "intereses_pagados": pesos(intereses_pagados),
        "intereses_pendientes": pesos(intereses_pend),
        "costas": pesos(costas),
        "otros": pesos(otros),
        "total": pesos(total),
        "supuestos": [
            "Interés del tramo = capital × tasa mensual × días / 30, con tasa mensual = (1 + EA)^(1/12) − 1.",
            "Los abonos se imputan primero a intereses y luego a capital (art. 1653 C.C.).",
            "La tasa debe ser la certificada para cada período y no exceder la de usura.",
        ],
        "advertencia": ADVERTENCIA,
    }


# --------------------------------------------------------------------------------------------
# Cuotas de administración (propiedad horizontal)
# --------------------------------------------------------------------------------------------
def _meses(inicial, final):
    y, m = inicial.year, inicial.month
    while (y, m) <= (final.year, final.month):
        yield y, m
        m += 1
        if m > 12:
            y, m = y + 1, 1


def liquidar_cuotas_administracion(
    valor_cuota, mes_inicial, mes_final, dia_vencimiento, fecha_corte, tasa_ea, extraordinarias=None, abonos_total=0
):
    """Cuotas de administración vencidas con intereses de mora (Ley 675 de 2001, art. 30).

    Cada cuota genera interés desde el día siguiente a su vencimiento hasta la fecha de corte:
    valor × tasa mensual × días de mora / 30. La ley fija el interés de mora en 1,5 veces el interés
    bancario corriente, salvo que la asamblea apruebe uno menor: digite la tasa EA que corresponda.
    """
    valor_cuota = _d(valor_cuota)
    if valor_cuota <= 0:
        raise ErrorLiquidacion("El valor de la cuota debe ser mayor que cero.")
    if mes_final < mes_inicial:
        raise ErrorLiquidacion("El último mes no puede ser anterior al primero.")
    if not 1 <= dia_vencimiento <= 28:
        raise ErrorLiquidacion("El día de vencimiento debe estar entre 1 y 28.")
    meses = list(_meses(mes_inicial, mes_final))
    if len(meses) > 120:
        raise ErrorLiquidacion("Máximo 120 cuotas por liquidación.")

    tm = tasa_mensual(tasa_ea)
    filas = []

    def fila(concepto, vencimiento, valor):
        if vencimiento > fecha_corte:
            return
        dias_mora = max(0, (fecha_corte - vencimiento).days)
        interes = _d(valor) * tm * dias_mora / 30
        filas.append(
            {
                "concepto": concepto,
                "vencimiento": _iso(vencimiento),
                "valor": pesos(valor),
                "dias_mora": dias_mora,
                "interes": pesos(interes),
                "total": pesos(valor) + pesos(interes),
            }
        )

    for y, m in meses:
        fila(f"Cuota de administración {y}-{m:02d}", date(y, m, dia_vencimiento), valor_cuota)
    for extra in extraordinarias or []:
        if _d(extra["valor"]) <= 0:
            raise ErrorLiquidacion("El valor de cada cuota extraordinaria debe ser mayor que cero.")
        fila(extra.get("concepto") or "Cuota extraordinaria", extra["fecha_vencimiento"], extra["valor"])

    if not filas:
        raise ErrorLiquidacion("Ninguna cuota está vencida a la fecha de corte.")

    capital = sum(f["valor"] for f in filas)
    intereses = sum(f["interes"] for f in filas)
    abonos = pesos(abonos_total or 0)
    return {
        "tipo": "cuotas",
        "filas": filas,
        "capital": capital,
        "intereses": intereses,
        "abonos": abonos,
        "total": capital + intereses - abonos,
        "supuestos": [
            "Interés de mora desde el día siguiente al vencimiento de cada cuota hasta la fecha de corte.",
            "Interés de la cuota = valor × tasa mensual × días de mora / 30, con tasa mensual = (1 + EA)^(1/12) − 1.",
            "Los abonos se restan del total; no se reparten entre cuotas.",
        ],
        "advertencia": ADVERTENCIA,
    }


# --------------------------------------------------------------------------------------------
# Liquidación de alimentos (cuotas alimentarias adeudadas)
# --------------------------------------------------------------------------------------------
def liquidar_alimentos(
    valor_cuota, mes_inicial, mes_final, dia_vencimiento, fecha_corte, tasa_ea=0, incremento_anual=0,
    adicionales=None, abonos_total=0,
):
    """Cuotas alimentarias adeudadas, con incremento anual y, si se indica, interés.

    - La cuota de cada año es la del primer año × (1 + incremento)^(años transcurridos), con el incremento
      aplicado cada 1 de enero (digite el IPC o el aumento que ordene la sentencia/acuerdo).
    - El interés (tasa EA digitada, 0 si no se cobra) corre desde el día siguiente al vencimiento de cada cuota
      hasta la fecha de corte: valor × tasa mensual × días de mora / 30.
    - `adicionales`: mesadas adicionales (prima, Navidad, útiles…) como {concepto, fecha_vencimiento, valor}.
    """
    valor_cuota = _d(valor_cuota)
    if valor_cuota <= 0:
        raise ErrorLiquidacion("El valor de la cuota debe ser mayor que cero.")
    if mes_final < mes_inicial:
        raise ErrorLiquidacion("El último mes no puede ser anterior al primero.")
    if not 1 <= dia_vencimiento <= 28:
        raise ErrorLiquidacion("El día de vencimiento debe estar entre 1 y 28.")
    meses = list(_meses(mes_inicial, mes_final))
    if len(meses) > 240:
        raise ErrorLiquidacion("Máximo 240 cuotas por liquidación.")
    incremento = _d(incremento_anual or 0) / Decimal(100)
    tm = tasa_mensual(tasa_ea or 0)
    filas = []

    def fila(concepto, vencimiento, valor):
        if vencimiento > fecha_corte:
            return
        dias_mora = max(0, (fecha_corte - vencimiento).days)
        interes = _d(valor) * tm * dias_mora / 30
        filas.append(
            {
                "concepto": concepto,
                "vencimiento": _iso(vencimiento),
                "valor": pesos(valor),
                "dias_mora": dias_mora,
                "interes": pesos(interes),
                "total": pesos(valor) + pesos(interes),
            }
        )

    primer_anio = mes_inicial.year
    for y, m in meses:
        cuota = valor_cuota * (Decimal(1) + incremento) ** (y - primer_anio)
        fila(f"Cuota alimentaria {y}-{m:02d}", date(y, m, dia_vencimiento), cuota)
    for extra in adicionales or []:
        if _d(extra["valor"]) <= 0:
            raise ErrorLiquidacion("El valor de cada mesada adicional debe ser mayor que cero.")
        fila(extra.get("concepto") or "Mesada adicional", extra["fecha_vencimiento"], extra["valor"])

    if not filas:
        raise ErrorLiquidacion("Ninguna cuota está vencida a la fecha de corte.")

    capital = sum(f["valor"] for f in filas)
    intereses = sum(f["interes"] for f in filas)
    abonos = pesos(abonos_total or 0)
    return {
        "tipo": "alimentos",
        "filas": filas,
        "capital": capital,
        "intereses": intereses,
        "abonos": abonos,
        "total": capital + intereses - abonos,
        "supuestos": [
            "La cuota se incrementa cada 1 de enero con el porcentaje digitado (0 si no hay incremento).",
            "Interés desde el día siguiente al vencimiento de cada cuota hasta la fecha de corte, con la tasa EA digitada (0 = sin interés).",
            "Los abonos se restan del total; no se reparten entre cuotas.",
            "Verifique el valor y el incremento con la sentencia, conciliación o acuerdo que fijó los alimentos.",
        ],
        "advertencia": ADVERTENCIA,
    }
