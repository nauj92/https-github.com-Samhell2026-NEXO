import { useEffect, useRef, useState } from "react";
import { ChevronDown } from "lucide-react";
import { inputStyle } from "./ui";

const sinAcentos = (t) => (t || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

/**
 * Lista desplegable con buscador, como los filtros de la Rama Judicial.
 * opciones: [{ value, label, grupo? }]. El primer elemento «vacío» (Todos / Sin asignar) limpia el valor.
 */
export default function SelectorBuscable({ opciones, value, onChange, vacio = "Todos", placeholder, required = false, vacioMensaje = "Sin resultados" }) {
  const [abierto, setAbierto] = useState(false);
  const [q, setQ] = useState("");
  const caja = useRef(null);

  useEffect(() => {
    if (!abierto) return undefined;
    const fuera = (e) => { if (caja.current && !caja.current.contains(e.target)) setAbierto(false); };
    const tecla = (e) => { if (e.key === "Escape") setAbierto(false); };
    document.addEventListener("mousedown", fuera);
    document.addEventListener("keydown", tecla);
    return () => { document.removeEventListener("mousedown", fuera); document.removeEventListener("keydown", tecla); };
  }, [abierto]);

  const elegida = opciones.find((o) => String(o.value) === String(value));
  const t = sinAcentos(q.trim());
  const visibles = t ? opciones.filter((o) => sinAcentos(`${o.label} ${o.grupo || ""}`).includes(t)) : opciones;

  const elegir = (v) => { onChange(v); setAbierto(false); setQ(""); };
  const item = (activo) => ({
    padding: "8px 12px", cursor: "pointer", fontSize: "13px", lineHeight: 1.35,
    background: activo ? "#5b9bff" : "transparent", color: activo ? "white" : "#2c3e50", fontWeight: activo ? 600 : 400,
  });

  let grupoActual = null;
  return (
    <div ref={caja} style={{ position: "relative" }}>
      <button
        type="button"
        onClick={() => setAbierto((a) => !a)}
        style={{ ...inputStyle, textAlign: "left", display: "flex", justifyContent: "space-between", alignItems: "center", gap: "8px", cursor: "pointer", background: "white", color: elegida ? "#2c3e50" : "#8899b4" }}
      >
        <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{elegida ? elegida.label : (placeholder || vacio)}</span>
        <ChevronDown size={16} />
      </button>
      {required && <input tabIndex={-1} aria-hidden="true" required value={value || ""} onChange={() => {}} style={{ position: "absolute", opacity: 0, height: 0, width: "100%", left: 0, bottom: 0, pointerEvents: "none" }} />}
      {abierto && (
        <div style={{ position: "absolute", zIndex: 30, left: 0, right: 0, top: "100%", marginTop: "4px", background: "white", border: "1px solid #d0d9e3", borderRadius: "8px", boxShadow: "0 8px 24px rgba(10,26,43,.18)" }}>
          <div style={{ padding: "8px" }}>
            <input autoFocus value={q} onChange={(e) => setQ(e.target.value)} placeholder="Buscar…" style={{ ...inputStyle, padding: "6px 8px" }} />
          </div>
          <div style={{ maxHeight: "220px", overflowY: "auto" }}>
            {!t && <div onClick={() => elegir("")} style={item(!value)}>{vacio}</div>}
            {visibles.map((o) => {
              const cabecera = o.grupo && o.grupo !== grupoActual ? (grupoActual = o.grupo) : null;
              return (
                <div key={`${o.grupo || ""}|${o.value}`}>
                  {cabecera && <div style={{ padding: "6px 12px", fontSize: "11px", fontWeight: 700, color: "#6b7f96", background: "#f4f7fb", letterSpacing: ".04em" }}>{cabecera}</div>}
                  <div onClick={() => elegir(o.value)} style={item(String(o.value) === String(value))}>{o.label}</div>
                </div>
              );
            })}
            {visibles.length === 0 && <div style={{ padding: "10px 12px", fontSize: "13px", color: "#6b7f96" }}>{vacioMensaje}</div>}
          </div>
        </div>
      )}
    </div>
  );
}
