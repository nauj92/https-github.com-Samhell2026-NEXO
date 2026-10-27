import { useMemo, useState } from "react";
import SelectorBuscable from "./SelectorBuscable";
import { Campo } from "./ui";
import { DEPARTAMENTOS, ENTIDADES, ESPECIALIDADES } from "../data/catalogos";

const unicos = (lista) => [...new Set(lista.filter(Boolean))];
const ordenar = (lista) => [...lista].sort((a, b) => a.localeCompare(b, "es"));
const opciones = (lista) => lista.map((x) => ({ value: x, label: x }));
const dosCol = { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 14px" };

/**
 * Filtros en cascada como en la Rama Judicial: Departamento > Municipio > Entidad > Especialidad > Despacho.
 * El Despacho se muestra como «código - NOMBRE». value = id del juzgado (o "").
 */
export default function SelectorDespacho({ juzgados, value, onChange, required = false, vacio = "Sin asignar", etiqueta = "Despacho" }) {
  const actual = juzgados.find((j) => String(j.id) === String(value));
  const [f, setF] = useState({
    departamento: actual?.departamento || "", municipio: actual?.municipio || "",
    entidad: actual?.entidad || "", especialidad: actual?.especialidad || "",
  });

  const coincide = (j, filtros) =>
    (!filtros.departamento || j.departamento === filtros.departamento) &&
    (!filtros.municipio || j.municipio === filtros.municipio) &&
    (!filtros.entidad || j.entidad === filtros.entidad) &&
    (!filtros.especialidad || j.especialidad === filtros.especialidad);

  const cambiar = (campo) => (v) => {
    const nuevo = { ...f, [campo]: v };
    if (campo === "departamento") nuevo.municipio = "";
    setF(nuevo);
    const sigue = actual && coincide(actual, nuevo);
    if (actual && !sigue) onChange("");
  };

  const lista = useMemo(() => juzgados.filter((j) => coincide(j, f)), [juzgados, f]); // eslint-disable-line react-hooks/exhaustive-deps
  const municipios = ordenar(unicos(juzgados.filter((j) => !f.departamento || j.departamento === f.departamento).map((j) => j.municipio)));
  const entidades = unicos([...ENTIDADES, ...juzgados.map((j) => j.entidad)]);
  const especialidades = unicos([...ESPECIALIDADES, ...juzgados.map((j) => j.especialidad)]);
  const departamentos = ordenar(unicos([...DEPARTAMENTOS, ...juzgados.map((j) => j.departamento)]));

  return (
    <div style={{ border: "1px solid #e9edf2", borderRadius: "10px", padding: "12px 12px 0", marginBottom: "14px", background: "#fcfdff" }}>
      <div style={{ fontSize: "12px", fontWeight: 700, color: "#6b7f96", marginBottom: "8px" }}>DESPACHO JUDICIAL (organizado como en la Rama Judicial)</div>
      <div style={dosCol}>
        <Campo label="Departamento"><SelectorBuscable opciones={opciones(departamentos)} value={f.departamento} onChange={cambiar("departamento")} /></Campo>
        <Campo label="Municipio"><SelectorBuscable opciones={opciones(municipios)} value={f.municipio} onChange={cambiar("municipio")} vacioMensaje="No hay municipios cargados" /></Campo>
        <Campo label="Entidad"><SelectorBuscable opciones={opciones(entidades)} value={f.entidad} onChange={cambiar("entidad")} /></Campo>
        <Campo label="Especialidad"><SelectorBuscable opciones={opciones(especialidades)} value={f.especialidad} onChange={cambiar("especialidad")} /></Campo>
      </div>
      <Campo label={`${etiqueta}${lista.length ? ` (${lista.length})` : ""}`}>
        <SelectorBuscable
          opciones={lista.map((j) => ({ value: j.id, label: j.etiqueta || j.nombre }))}
          value={value}
          onChange={onChange}
          vacio={vacio}
          required={required}
          vacioMensaje="No hay despachos con esos filtros"
        />
      </Campo>
    </div>
  );
}
