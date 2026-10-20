import { useEffect, useState } from "react";
import { FileText } from "lucide-react";
import api from "../api";
import Layout from "../components/Layout";
import { mensajeError } from "../utils/errores";
import { fecha, limpiar, pesos } from "../utils/formato";
import Borrador from "../components/Borrador";
import { Encabezado, Modal, Campo, Dato, Chip, Etiqueta, inputStyle, thStyle, tdStyle, botonSecundario, enlace, mensajeErrorEstilo } from "../components/ui";

const ESTADOS = {
  elaboracion: { label: "En elaboración", bg: "#e9ecf0", color: "#5b6f84" },
  radicada: { label: "Radicada", bg: "#e3effa", color: "#2a6aa8" },
  inadmitida: { label: "Inadmitida (subsanar)", bg: "#fff3d6", color: "#a8681a" },
  admitida: { label: "Admitida", bg: "#e2f3e8", color: "#1b8b5e" },
  rechazada: { label: "Rechazada", bg: "#fde8e8", color: "#c73a3a" },
  retirada: { label: "Retirada", bg: "#eee", color: "#777" },
};

const VACIO = {
  clase_proceso: "", cliente: "", expediente: "", juzgado: "", demandante: "", demandado: "", pretensiones: "",
  cuantia: "", estado: "elaboracion", fecha_radicacion: "", fecha_inadmision: "", fecha_admision: "",
  abogado_responsable: "", observaciones: "",
};

const hoyISO = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};

function textoSubsanacion(d) {
  if (!d.fecha_limite_subsanacion) return null;
  const dias = d.dias_para_subsanar;
  const cuando = dias < 0 ? `vencido hace ${-dias} d` : dias === 0 ? "vence hoy" : `faltan ${dias} d`;
  return { texto: `${fecha(d.fecha_limite_subsanacion)} (${cuando})`, color: dias < 0 ? "#c73a3a" : dias <= 2 ? "#a8681a" : "#1b8b5e" };
}

export default function Demandas() {
  const [demandas, setDemandas] = useState([]);
  const [clientes, setClientes] = useState([]);
  const [juzgados, setJuzgados] = useState([]);
  const [expedientes, setExpedientes] = useState([]);
  const [usuarios, setUsuarios] = useState([]);
  const [perfil, setPerfil] = useState(null);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(true);
  const [busqueda, setBusqueda] = useState("");
  const [filtro, setFiltro] = useState(null);
  const [form, setForm] = useState(null);
  const [editandoId, setEditandoId] = useState(null);
  const [formError, setFormError] = useState("");
  const [guardando, setGuardando] = useState(false);
  const [detalle, setDetalle] = useState(null);

  const cargar = () => {
    setCargando(true);
    api
      .get("/demandas/")
      .then((r) => setDemandas(r.data))
      .catch((err) => setError(mensajeError(err, "No se pudieron cargar las demandas.")))
      .finally(() => setCargando(false));
  };

  useEffect(() => {
    cargar();
    api.get("/clientes/").then((r) => setClientes(r.data)).catch(() => {});
    api.get("/juzgados/").then((r) => setJuzgados(r.data)).catch(() => {});
    api.get("/expedientes/").then((r) => setExpedientes(r.data)).catch(() => {});
    api.get("/usuarios/").then((r) => setUsuarios(r.data)).catch(() => {});
    api.get("/perfil/").then((r) => setPerfil(r.data)).catch(() => {});
  }, []);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const abrirNueva = () => {
    setForm({ ...VACIO });
    setEditandoId(null);
    setFormError("");
  };
  const abrirEditar = (d) => {
    setForm({
      clase_proceso: d.clase_proceso, cliente: d.cliente || "", expediente: d.expediente || "", juzgado: d.juzgado || "",
      demandante: d.demandante, demandado: d.demandado, pretensiones: d.pretensiones, cuantia: d.cuantia,
      estado: d.estado, fecha_radicacion: d.fecha_radicacion || "", fecha_inadmision: d.fecha_inadmision || "",
      fecha_admision: d.fecha_admision || "", abogado_responsable: d.abogado_responsable || "", observaciones: d.observaciones || "",
    });
    setEditandoId(d.id);
    setFormError("");
  };

  const guardar = async (e) => {
    e.preventDefault();
    setFormError("");
    setGuardando(true);
    try {
      const base = { ...form, cuantia: form.cuantia === "" ? "0" : form.cuantia };
      // En edición, los campos vacíos se envían como null para poder borrar una fecha o un vínculo
      const nulables = ["cliente", "expediente", "juzgado", "fecha_radicacion", "fecha_inadmision", "fecha_admision", "abogado_responsable"];
      let datos;
      if (editandoId) {
        datos = { ...base };
        nulables.forEach((k) => { if (datos[k] === "") datos[k] = null; });
      } else {
        datos = limpiar(base);
      }
      if (editandoId) await api.patch(`/demandas/${editandoId}/`, datos);
      else await api.post("/demandas/", datos);
      setForm(null);
      setEditandoId(null);
      cargar();
    } catch (err) {
      setFormError(mensajeError(err, "No se pudo guardar la demanda."));
    } finally {
      setGuardando(false);
    }
  };

  const eliminar = async (d) => {
    if (!window.confirm("¿Eliminar esta demanda? Esta acción no se puede deshacer.")) return;
    try {
      await api.delete(`/demandas/${d.id}/`);
      cargar();
    } catch (err) {
      alert(mensajeError(err, "No se pudo eliminar la demanda."));
    }
  };

  const conteo = (est) => demandas.filter((d) => d.estado === est).length;
  const porSubsanar = demandas.filter((d) => d.estado === "inadmitida" && d.dias_para_subsanar !== null && d.dias_para_subsanar <= 2).length;

  const visibles = demandas.filter((d) => {
    const t = busqueda.toLowerCase();
    const coincide = [d.demandante, d.demandado, d.clase_proceso, d.cliente_nombre || ""].some((x) => x.toLowerCase().includes(t));
    return coincide && (!filtro || d.estado === filtro);
  });

  const mostrarRadicacion = form && ["radicada", "inadmitida", "admitida", "rechazada"].includes(form.estado);

  return (
    <Layout>
      <div style={{ minHeight: "100vh", background: "#f4f7fb", fontFamily: "sans-serif" }}>
        <Encabezado Icono={FileText} titulo="A1 · Elaboración de demanda" busqueda={busqueda} setBusqueda={setBusqueda} placeholder="Buscar demanda..." textoBoton="+ Nueva demanda" onNuevo={abrirNueva} />
        <main style={{ padding: "32px" }}>
          {error && <p style={{ color: "#c73a3a" }}>{error}</p>}
          {cargando && <p>Cargando...</p>}
          {!cargando && !error && (
            <>
              <div style={{ display: "flex", gap: "10px", marginBottom: "20px", flexWrap: "wrap" }}>
                <Chip label={`Todas (${demandas.length})`} activo={!filtro} onClick={() => setFiltro(null)} />
                {Object.entries(ESTADOS).map(([k, v]) => (
                  <Chip key={k} label={`${v.label} (${conteo(k)})`} activo={filtro === k} onClick={() => setFiltro(filtro === k ? null : k)} bg={v.bg} color={v.color} />
                ))}
              </div>
              {porSubsanar > 0 && (
                <p style={{ background: "#fff3d6", color: "#a8681a", padding: "10px 14px", borderRadius: "10px", fontSize: "14px" }}>
                  ⚠ {porSubsanar} demanda(s) inadmitida(s) con el plazo de subsanación por vencer o vencido.
                </p>
              )}
              <div style={{ background: "white", borderRadius: "16px", border: "1px solid #eef2f6", overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
                  <thead>
                    <tr style={{ background: "#f8fafc" }}>
                      {["Proceso", "Partes", "Cuantía", "Estado", "Subsanar hasta", "Responsable", "Acción"].map((h) => (
                        <th key={h} style={thStyle}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {visibles.map((d) => {
                      const est = ESTADOS[d.estado] || ESTADOS.elaboracion;
                      const sub = textoSubsanacion(d);
                      return (
                        <tr key={d.id} style={{ borderTop: "1px solid #f0f3f8" }}>
                          <td style={tdStyle}>
                            <strong>{d.clase_proceso}</strong>
                            <div style={{ color: "#6b7f96", fontSize: "12px" }}>{d.expediente_numero || "Sin expediente"}</div>
                          </td>
                          <td style={tdStyle}>{d.demandante} <span style={{ color: "#6b7f96" }}>vs</span> {d.demandado}</td>
                          <td style={tdStyle}>{pesos(d.cuantia)}</td>
                          <td style={tdStyle}><Etiqueta texto={est.label} bg={est.bg} color={est.color} /></td>
                          <td style={tdStyle}>{sub ? <span style={{ color: sub.color, fontWeight: 600 }}>{sub.texto}</span> : "—"}</td>
                          <td style={tdStyle}>{d.abogado_nombre || "—"}</td>
                          <td style={tdStyle}>
                            <button style={enlace()} onClick={() => setDetalle(d)}>Ver</button>
                            <button style={enlace("#a8681a")} onClick={() => abrirEditar(d)}>Editar</button>
                            <button style={enlace("#c73a3a")} onClick={() => eliminar(d)}>Eliminar</button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                {visibles.length === 0 && (
                  <p style={{ padding: "24px", color: "#6b7f96" }}>{demandas.length === 0 ? "Aún no hay demandas registradas." : "No hay demandas que coincidan."}</p>
                )}
              </div>
            </>
          )}
        </main>

        {form && (
          <Modal onClose={() => setForm(null)} comoFormulario onSubmit={guardar} ancho={560}>
            <h2 style={{ marginTop: 0 }}>{editandoId ? "✏️ Editar demanda" : "+ Nueva demanda"}</h2>
            {formError && <p style={mensajeErrorEstilo}>{formError}</p>}
            <Campo label="Clase de proceso">
              <input value={form.clase_proceso} onChange={set("clase_proceso")} required placeholder="Ej.: Ejecutivo singular, Ordinario laboral" style={inputStyle} />
            </Campo>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 14px" }}>
              <Campo label="Demandante"><input value={form.demandante} onChange={set("demandante")} required style={inputStyle} /></Campo>
              <Campo label="Demandado"><input value={form.demandado} onChange={set("demandado")} required style={inputStyle} /></Campo>
            </div>
            <Campo label="Pretensiones">
              <textarea rows={3} value={form.pretensiones} onChange={set("pretensiones")} required placeholder="Qué se solicita al juez (mínimo 10 caracteres)" style={inputStyle} />
            </Campo>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 14px" }}>
              <Campo label="Cuantía (COP)"><input type="number" min="0" step="1" value={form.cuantia} onChange={set("cuantia")} style={inputStyle} /></Campo>
              <Campo label="Estado">
                <select value={form.estado} onChange={set("estado")} style={inputStyle}>
                  {Object.entries(ESTADOS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
                </select>
              </Campo>
            </div>
            {mostrarRadicacion && (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 14px" }}>
                <Campo label="Fecha de radicación"><input type="date" max={hoyISO()} value={form.fecha_radicacion} onChange={set("fecha_radicacion")} style={inputStyle} /></Campo>
                {form.estado === "inadmitida" && (
                  <Campo label="Fecha del auto que inadmite" ayuda="El plazo de 5 días hábiles para subsanar se calcula solo.">
                    <input type="date" value={form.fecha_inadmision} onChange={set("fecha_inadmision")} style={inputStyle} />
                  </Campo>
                )}
                {form.estado === "admitida" && (
                  <Campo label="Fecha del auto admisorio"><input type="date" value={form.fecha_admision} onChange={set("fecha_admision")} style={inputStyle} /></Campo>
                )}
              </div>
            )}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 14px" }}>
              <Campo label="Cliente">
                <select value={form.cliente} onChange={set("cliente")} style={inputStyle}>
                  <option value="">Sin cliente</option>
                  {clientes.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
                </select>
              </Campo>
              <Campo label="Juzgado">
                <select value={form.juzgado} onChange={set("juzgado")} style={inputStyle}>
                  <option value="">Sin asignar</option>
                  {juzgados.map((j) => <option key={j.id} value={j.id}>{j.nombre}</option>)}
                </select>
              </Campo>
            </div>
            <Campo label="Expediente (cuando ya exista)">
              <select value={form.expediente} onChange={set("expediente")} style={inputStyle}>
                <option value="">Sin expediente</option>
                {expedientes.map((x) => <option key={x.id} value={x.id}>{x.numero} · {x.demandante}</option>)}
              </select>
            </Campo>
            {perfil?.es_directivo && (
              <Campo label="Abogado responsable">
                <select value={form.abogado_responsable} onChange={set("abogado_responsable")} style={inputStyle}>
                  <option value="">Yo (por defecto)</option>
                  {usuarios.map((u) => <option key={u.id} value={u.id}>{u.nombre_completo}</option>)}
                </select>
              </Campo>
            )}
            <Campo label="Observaciones"><textarea rows={2} value={form.observaciones} onChange={set("observaciones")} style={inputStyle} /></Campo>
            <div style={{ display: "flex", gap: "10px", marginTop: "20px" }}>
              <button type="button" onClick={() => setForm(null)} style={{ ...botonSecundario, flex: 1 }}>Cancelar</button>
              <button type="submit" disabled={guardando} style={{ flex: 1, padding: "10px", borderRadius: "8px", border: "none", background: "#0a1a2b", color: "white", cursor: "pointer" }}>
                {guardando ? "Guardando..." : "Guardar"}
              </button>
            </div>
          </Modal>
        )}

        {detalle && (
          <Modal onClose={() => setDetalle(null)} ancho={640}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h2 style={{ margin: 0, fontSize: "18px" }}>{detalle.clase_proceso}</h2>
              <span onClick={() => setDetalle(null)} style={{ cursor: "pointer", fontSize: "22px" }}>&times;</span>
            </div>
            <p><Etiqueta texto={(ESTADOS[detalle.estado] || ESTADOS.elaboracion).label} bg={(ESTADOS[detalle.estado] || ESTADOS.elaboracion).bg} color={(ESTADOS[detalle.estado] || ESTADOS.elaboracion).color} /></p>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px", margin: "16px 0" }}>
              <Dato label="Demandante" value={detalle.demandante} />
              <Dato label="Demandado" value={detalle.demandado} />
              <Dato label="Cliente" value={detalle.cliente_nombre} />
              <Dato label="Juzgado" value={detalle.juzgado_nombre} />
              <Dato label="Cuantía" value={pesos(detalle.cuantia)} />
              <Dato label="Expediente" value={detalle.expediente_numero} />
              <Dato label="Radicación" value={fecha(detalle.fecha_radicacion)} />
              <Dato label="Responsable" value={detalle.abogado_nombre} />
              {detalle.estado === "inadmitida" && <Dato label="Auto de inadmisión" value={fecha(detalle.fecha_inadmision)} />}
              {detalle.estado === "inadmitida" && <Dato label="Subsanar hasta" value={textoSubsanacion(detalle)?.texto} />}
              {detalle.estado === "admitida" && <Dato label="Auto admisorio" value={fecha(detalle.fecha_admision)} />}
            </div>
            <Dato label="Pretensiones" value={<span style={{ whiteSpace: "pre-line" }}>{detalle.pretensiones}</span>} />
            <Borrador key={detalle.id} ruta={`/demandas/${detalle.id}`} inicial={detalle.borrador} nombreArchivo={`demanda-${detalle.id}`} onGuardado={cargar} />
            {detalle.observaciones && <div style={{ marginTop: "14px" }}><Dato label="Observaciones" value={<span style={{ whiteSpace: "pre-line" }}>{detalle.observaciones}</span>} /></div>}
          </Modal>
        )}
      </div>
    </Layout>
  );
}
