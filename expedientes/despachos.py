"""Interpretación de los despachos tal como los publica la Rama Judicial («código - NOMBRE»)."""
import re
import unicodedata

# El código de despacho de 12 dígitos se descompone así (igual que en el portal de la Rama Judicial):
#   DD MMM EE SS CCC  →  departamento, municipio, entidad, especialidad y consecutivo.
DEPARTAMENTOS = {
    "05": "ANTIOQUIA",
    "08": "ATLÁNTICO",
    "11": "BOGOTÁ",
    "13": "BOLÍVAR",
    "15": "BOYACÁ",
    "17": "CALDAS",
    "18": "CAQUETÁ",
    "19": "CAUCA",
    "20": "CESAR",
    "23": "CÓRDOBA",
    "25": "CUNDINAMARCA",
    "27": "CHOCÓ",
    "41": "HUILA",
    "44": "LA GUAJIRA",
    "47": "MAGDALENA",
    "50": "META",
    "52": "NARIÑO",
    "54": "NORTE DE SANTANDER",
    "63": "QUINDÍO",
    "66": "RISARALDA",
    "68": "SANTANDER",
    "70": "SUCRE",
    "73": "TOLIMA",
    "76": "VALLE DEL CAUCA",
    "81": "ARAUCA",
    "85": "CASANARE",
    "86": "PUTUMAYO",
    "88": "SAN ANDRÉS",
    "91": "AMAZONAS",
    "94": "GUAINÍA",
    "95": "GUAVIARE",
    "97": "VAUPÉS",
    "99": "VICHADA"
}

ENTIDADES = {
    "02": "CORTE SUPREMA DE JUSTICIA",
    "03": "CONSEJO DE ESTADO",
    "04": "CORTE CONSTITUCIONAL",
    "10": "CONSEJO SUPERIOR DE LA JUDICATURA",
    "12": "DIRECCION EJECUTIVA SECCIONAL DE ADMINISTRACION JUDICIAL DESAJ",
    "13": "CONSEJO SECCIONAL",
    "22": "TRIBUNAL SUPERIOR",
    "23": "TRIBUNAL ADMINISTRATIVO",
    "25": "COMISIÓN SECCIONAL DE DISCIPLINA JUDICIAL",
    "31": "JUZGADO DE CIRCUITO",
    "33": "JUZGADO ADMINISTRATIVO",
    "34": "JUZGADO CIRCUITO DE EJECUCIÓN",
    "40": "JUZGADO MUNICIPAL",
    "41": "JUZGADO DE PEQUEÑAS CAUSAS",
    "43": "JUZGADO MUNICIPAL DE EJECUCIÓN",
    "70": "CENTRO DE SERVICIOS ADMINISTRATIVOS",
    "71": "CENTRO DE SERVICIOS JUDICIALES"
}

ESPECIALIDADES = {
    "00": "CONSTITUCIONAL",
    "01": "ADMINISTRATIVA",
    "02": "DISCIPLINARIA",
    "03": "CIVIL",
    "04": "PENAL",
    "05": "LABORAL",
    "07": "PENAL ESPECIALIZADO",
    "08": "SALA ÚNICA",
    "09": "PENAL CON FUNCIÓN DE CONOCIMIENTO",
    "10": "FAMILIA",
    "12": "CIVIL - LABORAL",
    "13": "CIVIL - FAMILIA",
    "14": "CIVIL - FAMILIA - LABORAL",
    "15": "SECRETARÍA GENERAL",
    "18": "PENAL PARA ADOLESCENTES CON FUNCIÓN DE CONOCIMIENTO",
    "19": "PENAL JUSTICIA Y PAZ",
    "20": "PENAL ESPECIALIZADOS DE EXTINCIÓN DE DOMINIO",
    "21": "CIVIL RESTITUCIÓN DE TIERRAS",
    "24": "SECCIÓN PRIMERA",
    "25": "SECCIÓN SEGUNDA",
    "26": "SECCIÓN TERCERA",
    "27": "SECCIÓN CUARTA",
    "31": "SIN SECCIÓN",
    "32": "OFICINA JUDICIAL",
    "33": "SIN SECCIÓN - ORAL",
    "34": "SECCIÓN PRIMERA - ORAL",
    "35": "SECCIÓN SEGUNDA - ORAL",
    "36": "SECCIÓN TERCERA - ORAL",
    "37": "SECCIÓN CUARTA - ORAL",
    "39": "SECCIÓN ÚNICA MIXTA (ESCRIT-ORAL)",
    "40": "SIN SECCIÓN - MIXTA",
    "42": "SECCIÓN SEGUNDA MIXTA - ORAL",
    "43": "SECCIÓN TERCERA MIXTA - ORAL",
    "46": "PENAL MIXTO(LEYES 600, 906 Y 1098)",
    "53": "CIVIL ORALIDAD",
    "60": "FAMILIA ORALIDAD",
    "70": "CENTRO DE SERVICIOS ADMINISTRATIVOS",
    "71": "PENAL PARA ADOLESCENTES CON FUNCIÓN DE CONTROL DE GARANTÍAS",
    "72": "CENTRO DE SERVICIOS JUDICIALES",
    "82": "OFICINA DE SERVICIOS",
    "84": "PROMISCUO DE FAMILIA",
    "87": "EJECUCIÓN DE PENAS Y MEDIDAS DE SEGURIDAD",
    "88": "PENAL CON FUNCIÓN DE CONTROL DE GARANTÍAS",
    "89": "PROMISCUO / COMPETENCIA MÚLTIPLE",
    "98": "CONSEJO SUPERIOR"
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
    # Si lo que queda aún trae palabras del nombre del despacho, no es un municipio.
    if any(x in _sin_acentos(municipio).split() for x in ("JUZGADO", "JUZGADOS", "CIRCUITO", "SERVICIOS")):
        return ""
    # En los tribunales y altas cortes el texto final suele ser el departamento, no un municipio.
    if _sin_acentos(municipio) == _sin_acentos(departamento or "") and _sin_acentos(departamento) != "BOGOTA":
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
    # Entidad y especialidad salen del código (posiciones 6-7 y 8-9), como en el portal;
    # si el código trae un valor desconocido se deduce del nombre.
    entidad = ENTIDADES.get(codigo[5:7]) or _entidad(plano)
    especialidad = ESPECIALIDADES.get(codigo[7:9]) or _especialidad(plano)
    return {
        "codigo": codigo,
        "nombre": nombre,
        "departamento": departamento,
        "municipio": municipio,
        "entidad": entidad,
        "especialidad": especialidad,
        "ciudad": municipio or departamento.title(),
        "materia": especialidad.lower(),
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
    especialidad = _sin_acentos(_especialidad(plano))
    if numero is None or not especialidad:
        return []
    tipo = "MUNICIPAL" if "MUNICIPAL" in plano else ("CIRCUITO" if "CIRCUITO" in plano else "")
    especializado = "ESPECIALIZADO" in plano
    ejecucion = "EJECUCION" in plano
    pequenas = "PEQUENAS CAUSAS" in plano

    def filtrar(entidad):
        salida = []
        for n in nuevos:
            p = _sin_acentos(n.nombre)
            if _numero(n.nombre) != numero or especialidad not in _sin_acentos(n.especialidad):
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

    if pequenas:
        return filtrar("JUZGADO DE PEQUEÑAS CAUSAS")
    if tipo == "MUNICIPAL":
        return filtrar("JUZGADO MUNICIPAL DE EJECUCIÓN" if ejecucion else "JUZGADO MUNICIPAL")
    if tipo == "CIRCUITO":
        return filtrar("JUZGADO CIRCUITO DE EJECUCIÓN" if ejecucion else "JUZGADO DE CIRCUITO")
    # Sin tipo en el nombre: se prefiere el de circuito y, si no hay, el municipal.
    return filtrar("JUZGADO DE CIRCUITO") or filtrar("JUZGADO MUNICIPAL")
