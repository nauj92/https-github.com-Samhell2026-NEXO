import { useState } from "react";
import api from "../api";
import { mensajeError } from "../utils/errores";
import { Modal, Campo, inputStyle, botonSecundario, mensajeErrorEstilo } from "./ui";

export const TIPOS_DOC_CLIENTE = [["CC", "Cédula de ciudadanía"], ["CE", "Cédula de extranjería"], ["NIT", "NIT"], ["PA", "Pasaporte"]];
const VACIO = { nombre: "", tipo_documento: "CC", numero_documento: "", telefono: "", email: "", direccion: "" };
const dosCol = { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 14px" };

/** Ventana para crear (o editar, si llega `cliente`) un cliente. Devuelve el cliente guardado en `onGuardado`. */
export default function NuevoCliente({ cliente, onClose, onGuardado }) {
  const [form, setForm] = useState(cliente ? { ...VACIO, ...Object.fromEntries(Object.keys(VACIO).map((k) => [k, cliente[k] ?? ""])) } : { ...VACIO });
  const [error, setError] = useState("");
  const [guardando, setGuardando] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const guardar = async (e) => {
    e.preventDefault();
    setError("");
    setGuardando(true);
    try {
      const r = cliente ? await api.patch(`/clientes/${cliente.id}/`, form) : await api.post("/clientes/", form);
      onGuardado(r.data);
    } catch (err) {
      setError(mensajeError(err, "No se pudo guardar el cliente."));
    } finally {
      setGuardando(false);
    }
  };

  return (
    <Modal onClose={onClose} comoFormulario onSubmit={guardar} ancho={560}>
      <h2 style={{ marginTop: 0 }}>{cliente ? "✏️ Editar cliente" : "+ Nuevo cliente"}</h2>
      {error && <p style={mensajeErrorEstilo}>{error}</p>}
      <Campo label="Nombre completo o razón social"><input value={form.nombre} onChange={set("nombre")} required autoFocus style={inputStyle} /></Campo>
      <div style={dosCol}>
        <Campo label="Tipo de documento">
          <select value={form.tipo_documento} onChange={set("tipo_documento")} style={inputStyle}>
            {TIPOS_DOC_CLIENTE.map(([v, t]) => <option key={v} value={v}>{t}</option>)}
          </select>
        </Campo>
        <Campo label="Número de documento" ayuda={form.tipo_documento === "NIT" ? "Ej.: 900123456-7" : "Sin puntos"}>
          <input value={form.numero_documento} onChange={set("numero_documento")} required style={inputStyle} />
        </Campo>
        <Campo label="Teléfono"><input value={form.telefono} onChange={set("telefono")} placeholder="3001234567" style={inputStyle} /></Campo>
        <Campo label="Correo electrónico"><input type="email" value={form.email} onChange={set("email")} style={inputStyle} /></Campo>
      </div>
      <Campo label="Dirección"><input value={form.direccion} onChange={set("direccion")} style={inputStyle} /></Campo>
      <div style={{ display: "flex", gap: "10px", marginTop: "20px" }}>
        <button type="button" onClick={onClose} style={{ ...botonSecundario, flex: 1 }}>Cancelar</button>
        <button type="submit" disabled={guardando} style={{ flex: 1, padding: "10px", borderRadius: "8px", border: "none", background: "#0a1a2b", color: "white", cursor: "pointer" }}>
          {guardando ? "Guardando..." : "Guardar"}
        </button>
      </div>
    </Modal>
  );
}
