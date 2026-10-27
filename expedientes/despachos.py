"""Interpretación de los despachos tal como los publica la Rama Judicial («código - NOMBRE»)."""
import re
import unicodedata

# Los dos primeros dígitos del código de despacho son el código DANE del departamento.
DEPARTAMENTOS = {
    "05": "ANTIOQUIA", "08": "ATLÁNTICO", "11": "BOGOTÁ, D.C.", "13": "BOLÍVAR", "15": "BOYACÁ",
    "17": "CALDAS", "18": "CAQUETÁ", "19": "CAUCA", "20": "CESAR", "23": "CÓRDOBA",
    "25": "CUNDINAMARCA", "27": "CHOCÓ", "41": "HUILA", "44": "LA GUAJIRA", "47": "MAGDALENA",
    "50": "META", "52": "NARIÑO", "54": "NORTE DE SANTANDER", "63": "QUINDÍO", "66": "RISARALDA",
    "68": "SANTANDER", "70": "SUCRE", "73": "TOLIMA", "76": "VALLE DEL CAUCA", "81": "ARAUCA",
    "85": "CASANARE", "86": "PUTUMAYO", "88": "SAN ANDRÉS Y PROVIDENCIA", "91": "AMAZONAS",
    "94": "GUAINÍA", "95": "GUAVIARE", "97": "VAUPÉS", "99": "VICHADA",
}

_LINEA = re.compile(r"^\s*(\d{12})\s*-\s*(.+?)\s*$")
_MARCADORES = {
    "CIRCUITO", "MUNICIPAL", "CONOCIMIENTO", "SENTENCIAS", "SEGURIDAD", "CAUSAS", "GARANTIAS",
    "MULTIPLE", "FAMILIA", "LABORAL", "CIVIL", "PENAL", "ADMINISTRATIVO", "SUPERIOR", "ESPECIALIZADO",
    "TIERRAS", "PROMISCUO", "MENORES", "ADOLESCENTES", "COMERCIAL", "AGRARIO", "ADMINISTRATIVA",
}

# (texto que debe aparecer, etiqueta) — se aplica la primera coincidencia.
_ESPECIALIDADES = [
    ("CIVIL FAMILIA", "CIVIL FAMILIA"),
    ("PROMISCUO", "PROMISCUO / COMPETENCIA MÚLTIPLE"),
    ("COMPETENCIA MULTIPLE", "PROMISCUO / COMPETENCIA MÚLTIPLE"),
    ("PEQUENAS CAUSAS", "PEQUEÑAS CAUSAS Y COMPETENCIA MÚLTIPLE"),
    ("RESTITUCION DE TIERRAS", "RESTITUCIÓN DE TIERRAS"),
    ("FAMILIA", "FAMILIA"),
    ("LABORAL", "LABORAL"),
    ("PENAL", "PENAL"),
    ("CIVIL", "CIVIL"),
    ("ADMINISTRATIV", "ADMINISTRATIVA"),
    ("AGRARIO", "AGRARIA"),
    ("DISCIPLINARI", "DISCIPLINARIA"),
    ("CONSTITUCIONAL", "CONSTITUCIONAL"),
]


def _sin_acentos(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn").upper()


def _entidad(n):
    for clave, nombre in (
        ("CORTE SUPREMA", "CORTE SUPREMA DE JUSTICIA"),
        ("CORTE CONSTITUCIONAL", "CORTE CONSTITUCIONAL"),
        ("CONSEJO DE ESTADO", "CONSEJO DE ESTADO"),
        ("CENTRO DE SERVICIOS", "CENTRO DE SERVICIOS JUDICIALES"),
        ("TRIBUNAL ADMINISTRATIVO", "TRIBUNAL ADMINISTRATIVO"),
        ("TRIBUNAL SUPERIOR", "TRIBUNAL SUPERIOR"),
    ):
        if clave in n:
            return nombre
    if "JUZGADO" in n:
        if "ADMINISTRATIVO" in n:
            return "JUZGADO ADMINISTRATIVO"
        if "CIRCUITO" in n:
            return "JUZGADO DE CIRCUITO"
        if "MUNICIPAL" in n:
            return "JUZGADO MUNICIPAL"
        return "OTROS JUZGADOS"
    if n.startswith("SALA") and "TRIBUNAL" in n:
        return "TRIBUNAL SUPERIOR"
    return "OTRA ENTIDAD"


def _especialidad(n):
    for clave, nombre in _ESPECIALIDADES:
        if clave in n:
            return nombre
    return ""


def _municipio(nombre, departamento):
    tokens = nombre.split()
    plano = [_sin_acentos(t) for t in tokens]
    inicio = None
    for i in range(len(tokens) - 2, -1, -1):
        if plano[i] in _MARCADORES and plano[i + 1] in ("DE", "DEL"):
            inicio = i + 2
            break
    if inicio is None:
        for i in range(len(tokens) - 2, -1, -1):
            if plano[i] in ("DE", "DEL"):
                inicio = i + 1
                break
    if inicio is None:
        return ""
    municipio = " ".join(tokens[inicio:])
    # En los tribunales y altas cortes el texto final suele ser el departamento, no un municipio.
    if _sin_acentos(municipio) == _sin_acentos(departamento or ""):
        return ""
    return municipio


def interpretar_despacho(linea):
    """«110013109032 - JUZGADO 032 PENAL…» → dict con codigo, nombre, departamento, municipio, entidad, especialidad.

    Devuelve None si la línea no tiene el formato «12 dígitos - nombre».
    """
    m = _LINEA.match(linea or "")
    if not m:
        return None
    codigo, nombre = m.group(1), " ".join(m.group(2).split())
    plano = _sin_acentos(nombre)
    departamento = DEPARTAMENTOS.get(codigo[:2], "")
    municipio = _municipio(nombre, departamento)
    return {
        "codigo": codigo,
        "nombre": nombre,
        "departamento": departamento,
        "municipio": municipio,
        "entidad": _entidad(plano),
        "especialidad": _especialidad(plano),
        "ciudad": municipio or departamento.title(),
        "materia": _especialidad(plano).lower(),
    }


# ---------------------------------------------------------------------------
# Equivalencia entre un juzgado antiguo (nombre libre) y un despacho de la Rama Judicial
# ---------------------------------------------------------------------------
_EXCLUIDOS = ("EJECUCION", "PEQUENAS CAUSAS", "ADMINISTRATIVO", "RESTITUCION", "ADOLESCENTES", "GARANTIAS")


def _numero(nombre):
    m = re.search(r"JUZGADO\s+0*(\d+)", _sin_acentos(nombre))
    return int(m.group(1)) if m else None


def _ciudad_coincide(juzgado_viejo, nuevo):
    viejo = _sin_acentos(f"{juzgado_viejo.ciudad} {juzgado_viejo.nombre}").replace("D.C.", "")
    municipio = _sin_acentos(nuevo.municipio)
    return bool(municipio) and municipio in viejo


def candidatos_equivalentes(viejo, nuevos):
    """Despachos con código que corresponden a un juzgado antiguo. Devuelve la lista de candidatos."""
    plano = _sin_acentos(viejo.nombre)
    numero = _numero(viejo.nombre)
    especialidad = _especialidad(plano)
    if numero is None or not especialidad:
        return []
    tipo = "MUNICIPAL" if "MUNICIPAL" in plano else ("CIRCUITO" if "CIRCUITO" in plano else "")
    especializado = "ESPECIALIZADO" in plano

    def filtrar(entidad):
        salida = []
        for n in nuevos:
            p = _sin_acentos(n.nombre)
            if _numero(n.nombre) != numero or n.especialidad != especialidad:
                continue
            if entidad and n.entidad != entidad:
                continue
            if ("ESPECIALIZADO" in p) != especializado:
                continue
            if any((x in p) != (x in plano) for x in _EXCLUIDOS):
                continue
            if not _ciudad_coincide(viejo, n):
                continue
            salida.append(n)
        return salida

    if tipo == "MUNICIPAL":
        return filtrar("JUZGADO MUNICIPAL")
    if tipo == "CIRCUITO":
        return filtrar("JUZGADO DE CIRCUITO")
    # Sin tipo en el nombre: se prefiere el de circuito y, si no hay, el municipal.
    return filtrar("JUZGADO DE CIRCUITO") or filtrar("JUZGADO MUNICIPAL")
