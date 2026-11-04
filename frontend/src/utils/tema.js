// Modo diurno / nocturno: se recuerda en el navegador y se aplica en <html data-tema="...">.
const CLAVE = "tema";

export function temaGuardado() {
  try {
    return localStorage.getItem(CLAVE) === "oscuro" ? "oscuro" : "claro";
  } catch {
    return "claro"; // sin almacenamiento: modo diurno
  }
}

export function aplicarTema(tema) {
  const t = tema === "oscuro" ? "oscuro" : "claro";
  document.documentElement.setAttribute("data-tema", t);
  try {
    localStorage.setItem(CLAVE, t);
  } catch {
    /* sin almacenamiento: el cambio vale solo para esta visita */
  }
  return t;
}
