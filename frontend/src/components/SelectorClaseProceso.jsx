import { useState } from "react";
import SelectorBuscable from "./SelectorBuscable";
import { inputStyle } from "./ui";
import { CLASES_PROCESO, ESPECIALIDADES, todasLasClases } from "../data/catalogos";

const OTRA = "__otra__";

/** Clase de proceso: filtra por especialidad y elige de la lista; «Otra clase» permite escribirla. */
export default function SelectorClaseProceso({ value, onChange, required = false }) {
  const todas = todasLasClases();
  const enCatalogo = todas.some((c) => c.value === value);
  const [especialidad, setEspecialidad] = useState("");
  const [otra, setOtra] = useState(Boolean(value) && !enCatalogo);

  const grupos = Object.keys(CLASES_PROCESO);
  const lista = todas.filter((c) => !especialidad || c.grupo === especialidad);
  const especialidades = ESPECIALIDADES.filter((e) => grupos.includes(e));

  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 14px", marginBottom: "10px" }}>
        <div>
          <label style={{ fontSize: "12px", color: "#6b7f96", display: "block", marginBottom: "4px" }}>Especialidad</label>
          <SelectorBuscable opciones={especialidades.map((e) => ({ value: e, label: e }))} value={especialidad} onChange={setEspecialidad} />
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
