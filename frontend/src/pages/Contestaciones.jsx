import { useEffect, useState } from "react";
import { FileSignature } from "lucide-react";
import api from "../api";
import Layout from "../components/Layout";
import Borrador from "../components/Borrador";
import { mensajeError } from "../utils/errores";
import { fecha } from "../utils/formato";
import { Encabezado, Modal, Campo, Dato, Chip, Etiqueta, inputStyle, thStyle, tdStyle, botonSecundario, enlace, mensajeErrorEstilo } from "../components/ui";

const ESTADOS = {
  por_elaborar: { label: "Por elaborar", bg: "#e9ecf0", color: "#5b6f84" },
  en_elaboracion: { label: "En elaboración", bg: "#e3effa", color: "#2a6aa8" },
  presentada: { label: "Presentada", bg: "#e2f3e8", color: "#1b8b5e" },
  no_contestada: { label: "No contestada", bg: "#fde8e8", color: "#c73a3a" },
};

const VACIO = {
  clase_proceso: "", demandante: "", demandado: "", cliente: "", expediente: "", juzgado: "", fecha_notificacion: "",
  dias_termino: 20, estado: "por_elaborar", fecha_presentacion: "", excepciones: "", pruebas: "", abogado_responsable: "", observaciones: "",
};
const NULABLES = ["cliente", "expediente", "juzgado", "fecha_notificacion", "fecha_presentacion", "abogado_responsable"];

const hoyISO = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};

function textoLimite(c) {
  if (!c.fecha_limite) return null;
  const d = c.dias_restantes;
  if (d === null) return { texto: fecha(c.fecha_limite), color: "#6b7f96" };
  const cuando = d < 0 ? `vencido hace ${-d} d` : d === 0 ? "vence hoy" : `faltan ${d} d`;
  return { texto: `${fecha(c.fecha_limite)} (${cuando})`, color: d < 0 ? "#c73a3a" : d <= 3 ? "#a8681a" : "#1b8b5e" };
}

export default function Contestaciones() {
  const [lista, setLista] = useState([]);
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
      .get("/contestaciones/")
      .then((r) => setLista(r.data))
      .catch((err) => setError(mensajeError(err, "No se pudieron cargar las contestaciones.")))
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

  const abrirNueva = () => { setForm({ ...VACIO }); setEditandoId(null); setFormError(""); };
  const abrirEditar = (c) => {
    setForm({
      clase_proceso: c.clase_proceso, demandante: c.demandante, demandado: c.demandado, cliente: c.cliente || "",
      expediente: c.expediente || "", juzgado: c.juzgado || "", fecha_notificacion: c.fecha_notificacion || "",
      dias_termino: c.dias_termino, estado: c.estado, fecha_presentacion: c.fecha_presentacion || "",
      excepciones: c.excepciones || "", pruebas: c.pruebas || "", abogado_responsable: c.abogado_responsable || "",
      observaciones: c.observaciones || "",
    });
    setEditandoId(c.id);
    setFormError("");
  };

  const guardar = async (e) => {
    e.preventDefault();
    setFormError("");
    const dias = Number(form.dias_termino);
    if (!Number.isInteger(dias) || dias < 1 || dias > 90) return setFormError("El término debe estar entre 1 y 90 días hábiles.");
    setGuardando(true);
    try {
      const datos = { ...form, dias_termino: dias };
      NULABLES.forEach((k) => { if (datos[k] === "") { if (editandoId) datos[k] = null; else delete datos[k]; } });
      if (editandoId) await api.patch(`/contestaciones/${editandoId}/`, datos);
      else await api.post("/contestaciones/", datos);
      setForm(null);
      setEditandoId(null);
      cargar();
    } catch (err) {
      setFormError(mensajeError(err, "No se pudo guardar la contestación."));
    } finally {
      setGuardando(false);
    }
  };

  const eliminar = async (c) => {
    if (!window.confirm("¿Eliminar esta contestación? Esta acción no se puede deshacer.")) return;
    try {
      await api.delete(`/contestaciones/${c.id}/`);
      cargar();
    } catch (err) {
      alert(mensajeError(err, "No se pudo eliminar."));
    }
  };

  const conteo = (est) => lista.filter((c) => c.estado === est).length;
  const urgentes = lista.filter((c) => c.dias_restantes !== null && c.dias_restantes <= 3).length;
  const visibles = lista.filter((c) => {
    const t = busqueda.toLowerCase();
    const coincide = [c.demandante, c.demandado, c.clase_proceso, c.cliente_nombre || ""].some((x) => x.toLowerCase().includes(t));
    return coincide && (!filtro || c.estado === filtro);
  });

  return (
    <Layout>
      <div style={{ minHeight: "100vh", background: "#f4f7fb", fontFamily: "sans-serif" }}>
        <Encabezado Icono={FileSignature} titulo="B1 · Contestación de demanda" busqueda={busqueda} setBusqueda={setBusqueda} placeholder="Buscar contestación..." textoBoton="+ Nueva contestación" onNuevo={abrirNueva} />
        <main style={{ padding: "32px" }}>
          <p style={{ color: "#6b7f96", fontSize: "13px", marginTop: 0 }}>
            El plazo se cuenta en días hábiles desde la notificación (20 días por defecto en el proceso verbal; puede cambiarlo según la clase de proceso).
            Los festivos de Colombia se descuentan automáticamente; no se descuenta la vacancia judicial.
          </p>
          {error && <p style={{ color: "#c73a3a" }}>{error}</p>}
          {cargando && <p>Cargando...</p>}
          {!cargando && !error && (
            <>
              <div style={{ display: "flex", gap: "10px", marginBottom: "20px", flexWrap: "wrap" }}>
                <Chip label={`Todas (${lista.length})`} activo={!filtro} onClick={() => setFiltro(null)} />
                {Object.entries(ESTADOS).map(([k, v]) => (
                  <Chip key={k} label={`${v.label} (${conteo(k)})`} activo={filtro === k} onClick={() => setFiltro(filtro === k ? null : k)} bg={v.bg} color={v.color} />
                ))}
              </div>
              {urgentes > 0 && (
                <p style={{ background: "#fff3d6", color: "#a8681a", padding: "10px 14px", borderRadius: "10px", fontSize: "14px" }}>
                  ⚠ {urgentes} contestación(es) con el término vencido o por vencer en 3 días hábiles o menos.
                </p>
              )}
              <div style={{ background: "white", borderRadius: "16px", border: "1px solid #eef2f6", overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
                  <thead>
                    <tr style={{ background: "#f8fafc" }}>
                      {["Proceso", "Partes", "Notificación", "Vence", "Estado", "Responsable", "Acción"].map((h) => <th key={h} style={thStyle}>{h}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {visibles.map((c) => {
                      const est = ESTADOS[c.estado] || ESTADOS.por_elaborar;
                      const lim = textoLimite(c);
                      return (
                        <tr key={c.id} style={{ borderTop: "1px solid #f0f3f8" }}>
                          <td style={tdStyle}>
                            <strong>{c.clase_proceso}</strong>
                            <div style={{ color: "#6b7f96", fontSize: "12px" }}>{c.expediente_numero || "Sin expediente"}</div>
                          </td>
                          <td style={tdStyle}>{c.demandante} <span style={{ color: "#6b7f96" }}>vs</span> {c.demandado}</td>
                          <td style={tdStyle}>{fecha(c.fecha_notificacion)}</td>
                          <td style={tdStyle}>
                            {lim ? <span style={{ color: lim.color, fontWeight: 600 }}>{lim.texto}</span> : "—"}
                            {c.extemporanea && <div style={{ color: "#c73a3a", fontSize: "12px", fontWeight: 600 }}>Presentada fuera de término</div>}
                          </td>
                          <td style={tdStyle}><Etiqueta texto={est.label} bg={est.bg} color={est.color} /></td>
                          <td style={tdStyle}>{c.abogado_nombre || "—"}</td>
                          <td style={tdStyle}>
                            <button style={enlace()} onClick={() => setDetalle(c)}>Ver</button>
                            <button style={enlace("#a8681a")} onClick={() => abrirEditar(c)}>Editar</button>
                            <button style={enlace("#c73a3a")} onClick={() => eliminar(c)}>Eliminar</button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                {visibles.length === 0 && (
                  <p style={{ padding: "24px", color: "#6b7f96" }}>{lista.length === 0 ? "Aún no hay contestaciones registradas." : "No hay contestaciones que coincidan."}</p>
                )}
              </div>
            </>
          )}
        </main>

        {form && (
          <Modal onClose={() => setForm(null)} comoFormulario onSubmit={guardar} ancho={580}>
            <h2 style={{ marginTop: 0 }}>{editandoId ? "✏️ Editar contestación" : "+ Nueva contestación"}</h2>
            {formError && <p style={mensajeErrorEstilo}>{formError}</p>}
            <Campo label="Clase de proceso">
              <input value={form.clase_proceso} onChange={set("clase_proceso")} required placeholder="Ej.: Verbal, Ejecutivo, Ordinario laboral" style={inputStyle} />
            </Campo>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 14px" }}>
              <Campo label="Demandante"><input value={form.demandante} onChange={set("demandante")} required style={inputStyle} /></Campo>
              <Campo label="Demandado (quien contesta)"><input value={form.demandado} onChange={set("demandado")} required style={inputStyle} /></Campo>
              <Campo label="Fecha de notificación del demandado" ayuda="Con ella se calcula el vencimiento.">
                <input type="date" max={hoyISO()} value={form.fecha_notificacion} onChange={set("fecha_notificacion")} style={inputStyle} />
              </Campo>
              <Campo label="Término (días hábiles)"><input type="number" min="1" max="90" value={form.dias_termino} onChange={set("dias_termino")} style={inputStyle} /></Campo>
              <Campo label="Estado">
                <select value={form.estado} onChange={set("estado")} style={inputStyle}>
                  {Object.entries(ESTADOS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
                </select>
              </Campo>
              {form.estado === "presentada" && (
                <Campo label="Fecha de presentación"><input type="date" max={hoyISO()} value={form.fecha_presentacion} onChange={set("fecha_presentacion")} style={inputStyle} /></Campo>
              )}
            </div>
            <Campo label="Excepciones de mérito / previas"><textarea rows={3} value={form.excepciones} onChange={set("excepciones")} style={inputStyle} /></Campo>
            <Campo label="Pruebas que se solicitarán o aportarán"><textarea rows={2} value={form.pruebas} onChange={set("pruebas")} style={inputStyle} /></Campo>
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
            <Campo label="Expediente">
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
              <h2 style={{ margin: 0, fontSize: "18px" }}>Contestación · {detalle.clase_proceso}</h2>
              <span onClick={() => setDetalle(null)} style={{ cursor: "pointer", fontSize: "22px" }}>&times;</span>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px", margin: "16px 0" }}>
              <Dato label="Demandante" value={detalle.demandante} />
              <Dato label="Demandado" value={detalle.demandado} />
              <Dato label="Cliente" value={detalle.cliente_nombre} />
              <Dato label="Juzgado" value={detalle.juzgado_nombre} />
              <Dato label="Notificación" value={fecha(detalle.fecha_notificacion)} />
              <Dato label={`Vence (${detalle.dias_termino} días hábiles)`} value={textoLimite(detalle)?.texto} />
              <Dato label="Expediente" value={detalle.expediente_numero} />
              <Dato label="Responsable" value={detalle.abogado_nombre} />
              {detalle.estado === "presentada" && <Dato label="Presentada el" value={fecha(detalle.fecha_presentacion)} />}
            </div>
            {detalle.extemporanea && <p style={{ color: "#c73a3a", fontWeight: 600 }}>La contestación se presentó después del vencimiento del término.</p>}
            {detalle.excepciones && <Dato label="Excepciones" value={<span style={{ whiteSpace: "pre-line" }}>{detalle.excepciones}</span>} />}
            {detalle.pruebas && <div style={{ marginTop: "12px" }}><Dato label="Pruebas" value={<span style={{ whiteSpace: "pre-line" }}>{detalle.pruebas}</span>} /></div>}
            <Borrador key={detalle.id} ruta={`/contestaciones/${detalle.id}`} inicial={detalle.borrador} nombreArchivo={`contestacion-${detalle.id}`} onGuardado={cargar} />
          </Modal>
        )}
      </div>
    </Layout>
  );
}
