import { useState } from "react";
import api from "../api";
import { mensajeError } from "../utils/errores";
import { Etiqueta, enlace } from "./ui";

// Flujo de aprobación del abogado: borrador -> pendiente -> aprobado | devuelto (ver demandas/views.py)
const ESTILOS = {
  borrador: { bg: "#e9ecf0", color: "#5b6f84" },
  pendiente: { bg: "#fff3d6", color: "#a8681a" },
  aprobado: { bg: "#e2f3e8", color: "#1b8b5e" },
  devuelto: { bg: "#fde8e8", color: "#c73a3a" },
};

export function EtiquetaAprobacion({ item }) {
  const e = ESTILOS[item.aprobacion] || ESTILOS.borrador;
  return <Etiqueta texto={item.aprobacion_display || "Borrador"} bg={e.bg} color={e.color} />;
}

// Botones según el rol: quien edita envía a aprobación; quien aprueba (abogado) aprueba o devuelve.
// `recurso` es la ruta de la API (p. ej. "demandas"); `onCambio` recarga la lista.
export function AccionesAprobacion({ item, recurso, permiso, onCambio }) {
  const [ocupado, setOcupado] = useState(false);
  const ejecutar = async (accion, datos = {}) => {
    setOcupado(true);
    try {
      await api.post(`/${recurso}/${item.id}/${accion}/`, datos);
      onCambio();
    } catch (err) {
      alert(mensajeError(err, "No se pudo completar la acción."));
    } finally {
      setOcupado(false);
    }
  };
  const devolver = () => {
    const motivo = window.prompt("¿Qué debe ajustarse? (el motivo le llegará a quien lo envió)");
    if (motivo && motivo.trim()) ejecutar("devolver", { motivo: motivo.trim() });
  };
  const puedeEnviar = permiso.editar && ["borrador", "devuelto"].includes(item.aprobacion);
  const puedeResolver = permiso.aprobar && item.aprobacion === "pendiente";
  return (
    <>
      {puedeEnviar && (
        <button style={enlace("#1b6aa8")} disabled={ocupado} onClick={() => ejecutar("enviar")}>Enviar a aprobación</button>
      )}
      {puedeResolver && (
        <>
          <button style={enlace("#1b8b5e")} disabled={ocupado} onClick={() => ejecutar("aprobar")}>Aprobar</button>
          <button style={enlace("#c73a3a")} disabled={ocupado} onClick={devolver}>Devolver</button>
        </>
      )}
    </>
  );
}

export function MotivoDevolucion({ item }) {
  if (item.aprobacion !== "devuelto" || !item.motivo_devolucion) return null;
  return (
    <div style={{ fontSize: "12px", color: "#c73a3a", marginTop: "4px", maxWidth: "220px", whiteSpace: "pre-line" }}>
      Ajustar: {item.motivo_devolucion}
    </div>
  );
}
