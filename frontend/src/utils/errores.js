// Convierte un error de axios/DRF en un mensaje claro en español.
const ETIQUETAS = {
  numero: "Radicado",
  numero_documento: "Número de documento",
  tipo_documento: "Tipo de documento",
  nombre: "Nombre",
  demandante: "Demandante",
  demandado: "Demandado",
  juzgado: "Juzgado",
  cliente: "Cliente",
  expediente: "Expediente",
  abogado_asignado: "Abogado asignado",
  fecha: "Fecha",
  fecha_limite: "Fecha límite",
  dias_habiles: "Días hábiles",
  fecha_emision: "Fecha de emisión",
  fecha_vencimiento: "Fecha de vencimiento",
  monto: "Monto",
  lugar: "Lugar",
  telefono: "Teléfono",
  email: "Correo",
  username: "Usuario",
  first_name: "Nombre",
  last_name: "Apellido",
  rol: "Rol",
  password: "Contraseña",
  password_nueva: "Contraseña nueva",
  password_actual: "Contraseña actual",
  archivo: "Archivo",
  non_field_errors: "",
};

function aplanar(datos, prefijo = "") {
  if (datos == null) return [];
  if (typeof datos === "string") return [prefijo ? `${prefijo}: ${datos}` : datos];
  if (Array.isArray(datos)) return datos.flatMap((d) => aplanar(d, prefijo));
  if (typeof datos === "object") {
    return Object.entries(datos).flatMap(([campo, valor]) => {
      if (campo === "detail") return aplanar(valor, prefijo);
      const etiqueta = campo in ETIQUETAS ? ETIQUETAS[campo] : campo;
      return aplanar(valor, etiqueta);
    });
  }
  return [];
}

export function mensajeError(err, porDefecto = "No se pudo completar la operación.") {
  if (!err?.response) {
    return "No hay conexión con el servidor. Si el sistema estuvo inactivo puede tardar hasta un minuto en despertar; intente de nuevo.";
  }
  const { status, data } = err.response;
  if (status === 401) return "Su sesión expiró. Inicie sesión de nuevo.";
  if (status === 403) return (typeof data?.detail === "string" && data.detail) || "No tiene permiso para realizar esta acción.";
  if (status === 404) return "El registro no existe o ya fue eliminado.";
  if (status === 429) return "Demasiados intentos. Espere un momento e intente de nuevo.";
  if (status >= 500) return "Error del servidor. Intente de nuevo; si persiste, contacte al administrador.";
  const lineas = aplanar(data);
  return lineas.length ? lineas.join("\n") : porDefecto;
}
