import { useEffect, useState } from "react";
import { inputStyle } from "./ui";

const HORAS = Array.from({ length: 12 }, (_, i) => String(i + 1));
const MINUTOS = Array.from({ length: 60 }, (_, i) => String(i).padStart(2, "0"));

// "2026-11-09T19:35" -> { fecha, hora (1-12), minuto, jornada ("a" / "p") }
export function partirFechaHora(valor) {
  const m = /^(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2})/.exec(valor || "");
  if (!m) return { fecha: "", hora: "", minuto: "", jornada: "" };
  const h24 = Number(m[2]);
  return { fecha: m[1], hora: String(h24 % 12 || 12), minuto: m[3], jornada: h24 >= 12 ? "p" : "a" };
}

// Inverso: devuelve "" mientras falte alguna parte
export function unirFechaHora({ fecha, hora, minuto, jornada }) {
  if (!fecha || !hora || minuto === "" || !jornada) return "";
  const h = (Number(hora) % 12) + (jornada === "p" ? 12 : 0);
  return `${fecha}T${String(h).padStart(2, "0")}:${minuto}`;
}

/**
 * Fecha y hora en controles que se cierran al elegir: el calendario del navegador y tres listas
 * (hora, minuto, a. m./p. m.). Evita el selector combinado «datetime-local», que queda abierto.
 * value / onChange usan el formato "AAAA-MM-DDTHH:MM" (hora local).
 */
export default function CampoFechaHora({ value, onChange, required = false }) {
  const [p, setP] = useState(() => partirFechaHora(value));

  // Si el valor cambia desde afuera (editar otra audiencia, limpiar el formulario), se sincroniza
  useEffect(() => {
    if (unirFechaHora(p) !== (value || "")) setP(partirFechaHora(value));
  }, [value]); // eslint-disable-line react-hooks/exhaustive-deps

  const cambiar = (campo) => (e) => {
    const nuevo = { ...p, [campo]: e.target.value };
    setP(nuevo);
    onChange(unirFechaHora(nuevo));
  };

  return (
    <div>
      <input type="date" aria-label="Fecha" value={p.fecha} onChange={cambiar("fecha")} required={required} style={inputStyle} />
      <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1fr)", gap: "6px", marginTop: "6px" }}>
        <select aria-label="Hora" value={p.hora} onChange={cambiar("hora")} required={required} style={inputStyle}>
          <option value="">Hora</option>
          {HORAS.map((h) => <option key={h} value={h}>{h}</option>)}
        </select>
        <select aria-label="Minuto" value={p.minuto} onChange={cambiar("minuto")} required={required} style={inputStyle}>
          <option value="">Min</option>
          {MINUTOS.map((m) => <option key={m} value={m}>{m}</option>)}
        </select>
        <select aria-label="Jornada" value={p.jornada} onChange={cambiar("jornada")} required={required} style={inputStyle}>
          <option value="">a. m./p. m.</option>
          <option value="a">a. m.</option>
          <option value="p">p. m.</option>
        </select>
      </div>
    </div>
  );
}
