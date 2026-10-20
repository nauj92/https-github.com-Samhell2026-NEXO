import { Search } from "lucide-react";
import { Link } from "react-router-dom";

export const inputStyle = {
  width: "100%",
  padding: "8px 10px",
  borderRadius: "8px",
  border: "1px solid #d0d9e3",
  fontSize: "14px",
  boxSizing: "border-box",
};
export const thStyle = { textAlign: "left", padding: "14px 16px", color: "#6b7f96", fontWeight: 600, borderBottom: "1px solid #e9edf2" };
export const tdStyle = { padding: "12px 16px", verticalAlign: "top" };
export const botonPrimario = { background: "#0a1a2b", color: "white", border: "none", padding: "10px 20px", borderRadius: "30px", cursor: "pointer", fontWeight: 600, whiteSpace: "nowrap" };
export const botonSecundario = { padding: "10px 16px", borderRadius: "8px", border: "1px solid #d0d9e3", background: "white", cursor: "pointer" };
export const enlace = (color = "#1f3b57") => ({ color, fontWeight: 600, cursor: "pointer", textDecoration: "underline", marginRight: "12px", background: "none", border: "none", padding: 0, fontSize: "14px" });

export function Encabezado({ Icono, titulo, busqueda, setBusqueda, placeholder, textoBoton, onNuevo }) {
  return (
    <header style={{ background: "white", padding: "16px 32px", display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #e9edf2", gap: "12px", flexWrap: "wrap" }}>
      <div style={{ fontSize: "20px", fontWeight: "bold", display: "flex", alignItems: "center", gap: "10px" }}>
        {Icono && <Icono size={22} color="#0a1a2b" />}
        {titulo}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
        {setBusqueda && (
          <div style={{ background: "#f4f7fb", padding: "8px 16px", borderRadius: "30px", display: "flex", alignItems: "center", gap: "10px", border: "1px solid #e9edf2", width: "220px" }}>
            <Search size={16} color="#8899b4" />
            <input type="text" placeholder={placeholder} value={busqueda} onChange={(e) => setBusqueda(e.target.value)} style={{ border: "none", background: "transparent", outline: "none", fontSize: "14px", width: "100%" }} />
          </div>
        )}
        {onNuevo && (
          <button onClick={onNuevo} style={botonPrimario}>
            {textoBoton}
          </button>
        )}
      </div>
    </header>
  );
}

export function Modal({ onClose, ancho = 520, children, comoFormulario, onSubmit }) {
  const caja = { background: "white", borderRadius: "20px", padding: "28px", width: `${ancho}px`, maxWidth: "95vw", maxHeight: "88vh", overflowY: "auto" };
  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(10,26,43,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100 }} onClick={onClose}>
      {comoFormulario ? (
        <form onClick={(e) => e.stopPropagation()} onSubmit={onSubmit} style={caja}>
          {children}
        </form>
      ) : (
        <div onClick={(e) => e.stopPropagation()} style={caja}>
          {children}
        </div>
      )}
    </div>
  );
}

export function Campo({ label, children, ayuda }) {
  return (
    <div style={{ marginBottom: "14px" }}>
      <label style={{ fontSize: "13px", color: "#6b7f96", display: "block", marginBottom: "4px" }}>{label}</label>
      {children}
      {ayuda && <small style={{ color: "#6b7f96" }}>{ayuda}</small>}
    </div>
  );
}

export function Dato({ label, value }) {
  return (
    <div>
      <div style={{ fontSize: "11px", color: "#6b7f96", textTransform: "uppercase", letterSpacing: "0.5px" }}>{label}</div>
      <div style={{ fontWeight: 500, marginTop: "2px" }}>{value || "—"}</div>
    </div>
  );
}

export function Chip({ label, activo, onClick, bg = "#eef2f6", color = "#1a2c3e" }) {
  return (
    <span onClick={onClick} style={{ background: bg, color, padding: "6px 16px", borderRadius: "30px", fontSize: "13px", fontWeight: 600, cursor: "pointer", border: activo ? `2px solid ${color}` : "2px solid transparent" }}>
      {label}
    </span>
  );
}

export function Etiqueta({ texto, bg, color }) {
  return <span style={{ background: bg, color, padding: "4px 12px", borderRadius: "30px", fontSize: "12px", fontWeight: 600, whiteSpace: "nowrap" }}>{texto}</span>;
}

export function EnlaceExpedientes() {
  return (
    <p style={{ fontSize: "13px", color: "#6b7f96", margin: "0 0 14px" }}>
      ¿El proceso aún no está registrado? <Link to="/expedientes" style={{ color: "#1f3b57", fontWeight: 600 }}>Cree o consulte los expedientes aquí</Link>.
    </p>
  );
}

export const mensajeErrorEstilo = { color: "#c73a3a", fontSize: "13px", whiteSpace: "pre-line" };
