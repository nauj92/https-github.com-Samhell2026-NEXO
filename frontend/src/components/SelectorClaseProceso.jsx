import { useState } from "react";
import SelectorBuscable from "./SelectorBuscable";
import { inputStyle } from "./ui";
import { ESPECIALIDADES, gruposDeClases, todasLasClases } from "../data/catalogos";

const OTRA = "__otra__";

/** Clase de proceso: filtra por especialidad y elige de la lista; «Otra clase» permite escribirla. */
export default function SelectorClaseProceso({ value, onChange, required = false }) {
  const todas = todasLasClases();
  const enCatalogo = todas.some((c) => c.value === value);
  const [especialidad, setEspecialidad] = useState("");
  const [otra, setOtra] = useState(Boolean(value) && !enCatalogo);

  const grupos = gruposDeClases(especialidad);
  const lista = todas.filter((c) => grupos.includes(c.grupo));

  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 14px", marginBottom: "10px" }}>
        <div>
          <label style={{ fontSize: "12px", color: "#6b7f96", display: "block", marginBottom: "4px" }}>Especialidad</label>
          <SelectorBuscable opciones={ESPECIALIDADES.map((e) => ({ value: e, label: e }))} value={especialidad} onChange={setEspecialidad} />
        </div>
        <div>
          <label style={{ fontSize: "12px", color: "#6b7f96", display: "block", marginBottom: "4px" }}>Clase de proceso</label>
          <SelectorBuscable
            opciones={[...lista, { value: OTRA, label: "Otra clase (escribirla)", grupo: "OTRA" }]}
            value={otra ? OTRA : value}
            onChange={(v) => {
              if (v === OTRA) { setOtra(true); onChange(""); return; }
              setOtra(false);
              onChange(v);
            }}
            vacio="Seleccione una clase"
            vacioMensaje="Sin clases para esta especialidad: use «Otra clase»"
            required={required && !otra}
          />
        </div>
      </div>
      {otra && (
        <input value={value} onChange={(e) => onChange(e.target.value)} required={required} placeholder="Escriba la clase de proceso" style={inputStyle} />
      )}
    </div>
  );
}
