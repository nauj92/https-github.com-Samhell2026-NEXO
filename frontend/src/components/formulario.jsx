import { Etiqueta } from "./ui";

// Piezas compartidas por los formularios guiados por un artículo del CGP.

export const dosCol = { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 14px" };
export const TIPOS_PERSONA = [["natural", "Persona natural"], ["juridica", "Persona jurídica / patrimonio autónomo"]];
export const TIPOS_DOC = [["CC", "Cédula de ciudadanía"], ["CE", "Cédula de extranjería"], ["NIT", "NIT"], ["PAS", "Pasaporte"]];

export function Seccion({ numero, titulo, ayuda, children }) {
  return (
    <section style={{ border: "1px solid #e9edf2", borderRadius: "12px", padding: "14px 16px", marginBottom: "14px", background: "#fcfdfe" }}>
      <div style={{ fontWeight: 700, color: "#0a1a2b", marginBottom: ayuda ? "2px" : "10px" }}>
        {numero && <span style={{ color: "#a8681a" }}>{numero}. </span>}
        {titulo}
      </div>
      {ayuda && <div style={{ fontSize: "12px", color: "#6b7f96", marginBottom: "10px" }}>{ayuda}</div>}
      {children}
    </section>
  );
}

export function Casilla({ checked, onChange, children }) {
  return (
    <label style={{ fontSize: "14px", display: "flex", gap: "8px", alignItems: "center", margin: "6px 0 12px" }}>
      <input type="checkbox" checked={checked} onChange={onChange} />
      {children}
    </label>
  );
}

export function ChipRequisitos({ req }) {
  if (!req) return "—";
  const ok = req.cumplidos === req.total;
  const cerca = req.cumplidos >= req.total - 2;
  return <Etiqueta texto={`${req.cumplidos}/${req.total}`} bg={ok ? "#e2f3e8" : cerca ? "#fff3d6" : "#fde8e8"} color={ok ? "#1b8b5e" : cerca ? "#a8681a" : "#c73a3a"} />;
}
