// Formatos de presentación (Colombia)
export function pesos(valor) {
  if (valor === null || valor === undefined || valor === "") return "—";
  return new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(Number(valor));
}

// "2026-10-15" -> "15/10/2026" (sin pasar por Date para evitar corrimientos de zona horaria)
export function fecha(iso) {
  if (!iso) return "—";
  const [a, m, d] = String(iso).slice(0, 10).split("-");
  return `${d}/${m}/${a}`;
}

export function limpiar(obj) {
  // Quita los campos vacíos antes de enviar al servidor
  const salida = {};
  Object.entries(obj).forEach(([k, v]) => {
    if (v !== "" && v !== null && v !== undefined) salida[k] = v;
  });
  return salida;
}
