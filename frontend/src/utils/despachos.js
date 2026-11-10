// Reglas de los filtros de despacho (Departamento > Municipio > ...).

const sinAcentos = (t) => (t || "").normalize("NFD").replace(/[̀-ͯ]/g, "").trim().toLowerCase();
const unicos = (lista) => [...new Set(lista.filter(Boolean))];
const ordenar = (lista) => [...lista].sort((a, b) => a.localeCompare(b, "es"));

// «BOGOTÁ» (o «BOGOTÁ D.C.») como departamento
export const esDepartamentoBogota = (t) => sinAcentos(t).startsWith("bogota");
// «BOGOTÁ» (o «BOGOTÁ D.C.») como municipio; no incluye «BOGOTÁ ANTES J 11…», «EJECUCIÓN DE SENTENCIAS BOGOTÁ», etc.
export const esMunicipioBogota = (t) => /^bogota( d\.? ?c\.?)?$/.test(sinAcentos(t));

/**
 * Municipios para elegir según el departamento. Si el departamento es Bogotá, solo se ofrece Bogotá
 * (y, al editar, el municipio que ya tenga guardado el registro para no perderlo).
 */
export function municipiosDe(juzgados, departamento, municipioActual = "") {
  const todos = ordenar(unicos(juzgados.filter((j) => !departamento || j.departamento === departamento).map((j) => j.municipio)));
  if (!esDepartamentoBogota(departamento)) return todos;
  const bogota = todos.filter(esMunicipioBogota);
  if (!bogota.length) return todos;
  return municipioActual && !bogota.includes(municipioActual) ? [...bogota, municipioActual] : bogota;
}

// Municipio que se elige solo al escoger un departamento (hoy: Bogotá → Bogotá); "" si no aplica.
export function municipioAutomatico(juzgados, departamento) {
  if (!esDepartamentoBogota(departamento)) return "";
  return municipiosDe(juzgados, departamento).find(esMunicipioBogota) || "";
}
