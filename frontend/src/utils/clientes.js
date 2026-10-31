// Datos de un cliente registrado, listos para completar a una parte del proceso (demandante o demandado).
export function clienteComoParte(c, parte) {
  return {
    [parte]: c.nombre,
    [`${parte}_tipo_persona`]: c.tipo_documento === "NIT" ? "juridica" : "natural",
    [`${parte}_tipo_documento`]: c.tipo_documento === "PA" ? "PAS" : c.tipo_documento,
    [`${parte}_documento`]: c.numero_documento,
    [`notif_${parte}_email`]: c.email || "",
    [`notif_${parte}_direccion`]: c.direccion || "",
  };
}

// Completa solo los campos que estén vacíos, para no pisar lo que el usuario ya escribió.
export function completarVacios(form, nuevos) {
  const resultado = { ...form };
  Object.entries(nuevos).forEach(([k, v]) => {
    if ((resultado[k] === "" || resultado[k] === undefined || resultado[k] === null) && v !== "") resultado[k] = v;
  });
  return resultado;
}

export const ordenarPorNombre = (lista) => [...lista].sort((a, b) => a.nombre.localeCompare(b.nombre, "es"));

// Selecciona al cliente y, si la parte aún está vacía, la completa con sus datos (identificación y notificaciones).
export function aplicarClienteAParte(form, c, parte) {
  const datos = clienteComoParte(c, parte);
  const base = { ...form, cliente: c.id };
  if (form[parte] || form[`${parte}_documento`]) return base;
  [parte, `${parte}_tipo_persona`, `${parte}_tipo_documento`, `${parte}_documento`].forEach((k) => { base[k] = datos[k]; });
  return completarVacios(base, datos);
}
