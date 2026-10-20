import { useEffect, useState } from "react";
import { Eye } from "lucide-react";
import api from "../api";
import Layout from "../components/Layout";
import { mensajeError } from "../utils/errores";
import { fecha } from "../utils/formato";
import { EnlaceExpedientes, Encabezado, Modal, Campo, Chip, Etiqueta, inputStyle, thStyle, tdStyle, botonSecundario, enlace, mensajeErrorEstilo } from "../components/ui";

const hoyISO = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};

export default function Vigilancia() {
  const [vigilancias, setVigilancias] = useState([]);
  const [expedientes, setExpedientes] = useState([]);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(true);
  const [busqueda, setBusqueda] = useState("");
  const [filtro, setFiltro] = useState("todas"); // todas | alerta | activas
  const [form, setForm] = useState(null); // alta o edición
  const [formError, setFormError] = useState("");
  const [guardando, setGuardando] = useState(false);
  const [detalle, setDetalle] = useState(null);
  const [actuaciones, setActuaciones] = useState([]);
  const [nueva, setNueva] = useState({ fecha: hoyISO(), descripcion: "" });
  const [errorAct, setErrorAct] = useState("");
  const [pestana, setPestana] = useState("enlaces"); // enlaces | actuaciones
  const [enlaces, setEnlaces] = useState([]);
  const [nuevoEnlace, setNuevoEnlace] = useState({ titulo: "", url: "https://", nota: "" });
  const [errorEnl, setErrorEnl] = useState("");

  const cargar = () => {
    setCargando(true);
    api
      .get("/vigilancia/")
      .then((r) => setVigilancias(r.data))
      .catch((err) => setError(mensajeError(err, "No se pudo cargar la vigilancia.")))
      .finally(() => setCargando(false));
  };

  useEffect(() => {
    cargar();
    api.get("/expedientes/").then((r) => setExpedientes(r.data)).catch(() => {});
  }, []);

  const yaVigilados = new Set(vigilancias.map((v) => v.expediente));
  const disponibles = expedientes.filter((e) => !yaVigilados.has(e.id) && e.estado !== "cerrado");

  const visibles = vigilancias.filter((v) => {
    const t = busqueda.toLowerCase();
    const coincide = v.expediente_numero.toLowerCase().includes(t) || (v.juzgado_nombre || "").toLowerCase().includes(t) ||
      (v.demandante || "").toLowerCase().includes(t) || (v.demandado || "").toLowerCase().includes(t);
    const pasa = filtro === "todas" || (filtro === "alerta" && v.alerta) || (filtro === "activas" && v.activa);
    return coincide && pasa;
  });
  const enAlerta = vigilancias.filter((v) => v.alerta).length;

  const abrirNuevo = () => {
    setForm({ id: null, expediente: "", dias_alerta: 30, observaciones: "", activa: true });
    setFormError("");
  };
  const abrirEditar = (v) => {
    setForm({ id: v.id, expediente: v.expediente, dias_alerta: v.dias_alerta, observaciones: v.observaciones || "", activa: v.activa });
    setFormError("");
  };

  const guardar = async (e) => {
    e.preventDefault();
    setFormError("");
    if (!form.id && !form.expediente) return setFormError("Seleccione el proceso que desea vigilar.");
    const dias = Number(form.dias_alerta);
    if (!Number.isInteger(dias) || dias < 1 || dias > 365) return setFormError("Los días de alerta deben estar entre 1 y 365.");
    setGuardando(true);
    try {
      const datos = { dias_alerta: dias, observaciones: form.observaciones, activa: form.activa };
      if (form.id) await api.patch(`/vigilancia/${form.id}/`, datos);
      else await api.post("/vigilancia/", { ...datos, expediente: Number(form.expediente) });
      setForm(null);
      cargar();
    } catch (err) {
      setFormError(mensajeError(err, "No se pudo guardar."));
    } finally {
      setGuardando(false);
    }
  };

  const eliminar = async (v) => {
    if (!window.confirm(`¿Dejar de vigilar el proceso ${v.expediente_numero}? Se borrarán sus actuaciones registradas.`)) return;
    try {
      await api.delete(`/vigilancia/${v.id}/`);
      cargar();
    } catch (err) {
      alert(mensajeError(err, "No se pudo eliminar."));
    }
  };

  const abrirActuaciones = (v) => {
    setDetalle(v);
    setActuaciones([]);
    setErrorAct("");
    setNueva({ fecha: hoyISO(), descripcion: "" });
    setPestana("enlaces");
    setEnlaces([]);
    setErrorEnl("");
    setNuevoEnlace({ titulo: "", url: "https://", nota: "" });
    api.get(`/vigilancia/${v.id}/actuaciones/`).then((r) => setActuaciones(r.data)).catch(() => {});
    api.get(`/vigilancia/${v.id}/enlaces/`).then((r) => setEnlaces(r.data)).catch(() => {});
  };

  const recargarEnlaces = async () => {
    const [l, v] = await Promise.all([api.get(`/vigilancia/${detalle.id}/enlaces/`), api.get(`/vigilancia/${detalle.id}/`)]);
    setEnlaces(l.data);
    setDetalle(v.data);
    cargar();
  };

  const anclarEnlace = async (e) => {
    e.preventDefault();
    setErrorEnl("");
    try {
      await api.post(`/vigilancia/${detalle.id}/enlaces/`, nuevoEnlace);
      setNuevoEnlace({ titulo: "", url: "https://", nota: "" });
      await recargarEnlaces();
    } catch (err) {
      setErrorEnl(mensajeError(err, "No se pudo anclar el enlace."));
    }
  };

  const quitarEnlace = async (l) => {
    if (!window.confirm("¿Quitar este enlace?")) return;
    try {
      await api.delete(`/vigilancia/${detalle.id}/enlace/${l.id}/`);
      await recargarEnlaces();
    } catch (err) {
      setErrorEnl(mensajeError(err, "No se pudo quitar el enlace."));
    }
  };

  const recargarDetalle = async () => {
    const [a, v] = await Promise.all([api.get(`/vigilancia/${detalle.id}/actuaciones/`), api.get(`/vigilancia/${detalle.id}/`)]);
    setActuaciones(a.data);
    setDetalle(v.data);
    cargar();
  };

  const registrar = async (e) => {
    e.preventDefault();
    setErrorAct("");
    if (nueva.descripcion.trim().length < 5) return setErrorAct("Describa la actuación (mínimo 5 caracteres).");
    try {
      await api.post(`/vigilancia/${detalle.id}/actuaciones/`, nueva);
      setNueva({ fecha: hoyISO(), descripcion: "" });
      await recargarDetalle();
    } catch (err) {
      setErrorAct(mensajeError(err, "No se pudo registrar la actuación."));
    }
  };

  const borrarActuacion = async (a) => {
    if (!window.confirm("¿Eliminar esta actuación?")) return;
    try {
      await api.delete(`/vigilancia/${detalle.id}/actuaciones/${a.id}/`);
      await recargarDetalle();
    } catch (err) {
      setErrorAct(mensajeError(err, "No se pudo eliminar la actuación."));
    }
  };

  return (
    <Layout>
      <div style={{ minHeight: "100vh", background: "#f4f7fb", fontFamily: "sans-serif" }}>
        <Encabezado Icono={Eye} titulo="Vigilancia Judicial" busqueda={busqueda} setBusqueda={setBusqueda} placeholder="Buscar proceso..." textoBoton="+ Vigilar proceso" onNuevo={abrirNuevo} />
        <main style={{ padding: "32px" }}>
          <p style={{ color: "#6b7f96", fontSize: "13px", marginTop: 0 }}>
            Ancle a cada proceso los enlaces que necesite (consulta de procesos, estados electrónicos, expediente digital) y registre las actuaciones que vaya conociendo; el sistema avisa cuando un proceso pasa demasiado tiempo sin movimiento. No se conecta a la Rama Judicial.
          </p>
          <EnlaceExpedientes />
          {error && <p style={{ color: "#c73a3a" }}>{error}</p>}
          {cargando && <p>Cargando...</p>}
          {!cargando && !error && (
            <>
              <div style={{ display: "flex", gap: "10px", marginBottom: "20px", flexWrap: "wrap" }}>
                <Chip label={`Todas (${vigilancias.length})`} activo={filtro === "todas"} onClick={() => setFiltro("todas")} />
                <Chip label={`Sin movimiento (${enAlerta})`} activo={filtro === "alerta"} onClick={() => setFiltro("alerta")} bg="#fde8e8" color="#c73a3a" />
                <Chip label="Activas" activo={filtro === "activas"} onClick={() => setFiltro("activas")} bg="#e2f3e8" color="#1b8b5e" />
              </div>
              <div style={{ background: "white", borderRadius: "16px", border: "1px solid #eef2f6", overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
                  <thead>
                    <tr style={{ background: "#f8fafc" }}>
                      {["Proceso", "Partes", "Última actuación", "Sin movimiento", "Estado", "Acción"].map((h) => (
                        <th key={h} style={thStyle}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {visibles.map((v) => (
                      <tr key={v.id} style={{ borderTop: "1px solid #f0f3f8" }}>
                        <td style={tdStyle}>
                          <strong>{v.expediente_numero}</strong>
                          <div style={{ color: "#6b7f96", fontSize: "12px" }}>{v.juzgado_nombre}</div>
                        </td>
                        <td style={tdStyle}>{v.demandante} <span style={{ color: "#6b7f96" }}>vs</span> {v.demandado}</td>
                        <td style={tdStyle}>
                          {v.ultima_actuacion ? (
                            <>
                              <strong>{fecha(v.ultima_actuacion)}</strong>
                              <div style={{ color: "#6b7f96", fontSize: "12px" }}>{v.ultima_descripcion}</div>
                            </>
                          ) : (
                            <span style={{ color: "#6b7f96" }}>Sin actuaciones</span>
                          )}
                        </td>
                        <td style={tdStyle}>
                          <span style={{ fontWeight: 700, color: v.alerta ? "#c73a3a" : "#1b8b5e" }}>{v.dias_sin_movimiento} días</span>
                          <div style={{ color: "#6b7f96", fontSize: "12px" }}>alerta a los {v.dias_alerta}</div>
                        </td>
                        <td style={tdStyle}>
                          {!v.activa ? <Etiqueta texto="Pausada" bg="#e9ecf0" color="#5b6f84" /> : v.alerta ? <Etiqueta texto="Sin movimiento" bg="#fde8e8" color="#c73a3a" /> : <Etiqueta texto="Al día" bg="#e2f3e8" color="#1b8b5e" />}
                        </td>
                        <td style={tdStyle}>
                          <button style={enlace()} onClick={() => abrirActuaciones(v)}>Enlaces ({v.total_enlaces ?? 0}) y actuaciones ({v.total_actuaciones})</button>
                          <button style={enlace("#a8681a")} onClick={() => abrirEditar(v)}>Editar</button>
                          <button style={enlace("#c73a3a")} onClick={() => eliminar(v)}>Quitar</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {visibles.length === 0 && (
                  <p style={{ padding: "24px", color: "#6b7f96" }}>
                    {vigilancias.length === 0 ? "Aún no vigila ningún proceso. Use “+ Vigilar proceso”." : "No hay procesos que coincidan."}
                  </p>
                )}
              </div>
            </>
          )}
        </main>

        {form && (
          <Modal onClose={() => setForm(null)} comoFormulario onSubmit={guardar} ancho={440}>
            <h2 style={{ marginTop: 0 }}>{form.id ? "Editar vigilancia" : "Vigilar un proceso"}</h2>
            {formError && <p style={mensajeErrorEstilo}>{formError}</p>}
            {!form.id && (
              <Campo label="Proceso (expediente)">
                <select value={form.expediente} onChange={(e) => setForm({ ...form, expediente: e.target.value })} style={inputStyle}>
                  <option value="">Seleccione un expediente</option>
                  {disponibles.map((e) => (
                    <option key={e.id} value={e.id}>{e.numero} · {e.demandante}</option>
                  ))}
                </select>
              </Campo>
            )}
            <Campo label="Avisar si pasan estos días sin movimiento" ayuda="Entre 1 y 365 días.">
              <input type="number" min="1" max="365" value={form.dias_alerta} onChange={(e) => setForm({ ...form, dias_alerta: e.target.value })} style={inputStyle} />
            </Campo>
            <Campo label="Observaciones">
              <textarea rows={3} value={form.observaciones} onChange={(e) => setForm({ ...form, observaciones: e.target.value })} style={inputStyle} />
            </Campo>
            <label style={{ fontSize: "14px", display: "flex", gap: "8px", alignItems: "center" }}>
              <input type="checkbox" checked={form.activa} onChange={(e) => setForm({ ...form, activa: e.target.checked })} />
              Vigilancia activa (si la pausa, no genera alertas)
            </label>
            <div style={{ display: "flex", gap: "10px", marginTop: "20px" }}>
              <button type="button" onClick={() => setForm(null)} style={{ ...botonSecundario, flex: 1 }}>Cancelar</button>
              <button type="submit" disabled={guardando} style={{ flex: 1, padding: "10px", borderRadius: "8px", border: "none", background: "#0a1a2b", color: "white", cursor: "pointer" }}>
                {guardando ? "Guardando..." : "Guardar"}
              </button>
            </div>
          </Modal>
        )}

        {detalle && (
          <Modal onClose={() => setDetalle(null)} ancho={560}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h2 style={{ margin: 0, fontSize: "18px" }}>Vigilancia · {detalle.expediente_numero}</h2>
              <span onClick={() => setDetalle(null)} style={{ cursor: "pointer", fontSize: "22px" }}>&times;</span>
            </div>
            <p style={{ color: "#6b7f96", fontSize: "13px" }}>{detalle.demandante} vs {detalle.demandado} · {detalle.juzgado_nombre}</p>
            <div style={{ display: "flex", gap: "10px", margin: "10px 0" }}>
              <Chip label={`Enlaces anclados (${enlaces.length})`} activo={pestana === "enlaces"} onClick={() => setPestana("enlaces")} />
              <Chip label={`Actuaciones (${actuaciones.length})`} activo={pestana === "actuaciones"} onClick={() => setPestana("actuaciones")} />
            </div>
            {pestana === "enlaces" && (
              <>
                <form onSubmit={anclarEnlace} style={{ display: "grid", gap: "8px", margin: "14px 0" }}>
                  <input type="text" placeholder="Título (ej.: Consulta de procesos Rama Judicial)" value={nuevoEnlace.titulo} onChange={(e) => setNuevoEnlace({ ...nuevoEnlace, titulo: e.target.value })} required maxLength={150} style={inputStyle} />
                  <input type="url" placeholder="https://..." value={nuevoEnlace.url} onChange={(e) => setNuevoEnlace({ ...nuevoEnlace, url: e.target.value })} required style={inputStyle} />
                  <input type="text" placeholder="Nota (opcional)" value={nuevoEnlace.nota} onChange={(e) => setNuevoEnlace({ ...nuevoEnlace, nota: e.target.value })} maxLength={255} style={inputStyle} />
                  <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                    <button type="submit" style={{ padding: "8px 14px", borderRadius: "8px", border: "none", background: "#0a1a2b", color: "white", cursor: "pointer" }}>Anclar enlace</button>
                    <button type="button" style={botonSecundario} onClick={() => setNuevoEnlace({ titulo: "Consulta de procesos – Rama Judicial", url: "https://consultaprocesos.ramajudicial.gov.co/", nota: `Radicado ${detalle.expediente_numero}` })}>
                      Usar enlace de la Rama Judicial
                    </button>
                  </div>
                </form>
                {errorEnl && <p style={mensajeErrorEstilo}>{errorEnl}</p>}
                {enlaces.length === 0 && <p style={{ color: "#6b7f96", fontSize: "13px" }}>Aún no hay enlaces anclados a este proceso.</p>}
                {enlaces.map((l) => (
                  <div key={l.id} style={{ display: "flex", justifyContent: "space-between", gap: "10px", padding: "10px 0", borderBottom: "1px dashed #e9edf2", fontSize: "14px" }}>
                    <span style={{ minWidth: 0 }}>
                      <a href={l.url} target="_blank" rel="noopener noreferrer" style={{ fontWeight: 600, color: "#1f3b57", wordBreak: "break-all" }}>{l.titulo}</a>
                      {l.nota && <div style={{ color: "#6b7f96", fontSize: "12px" }}>{l.nota}</div>}
                      <div style={{ color: "#6b7f96", fontSize: "12px" }}>Anclado por {l.creado_por_nombre || "—"} · {fecha(l.creado_en)}</div>
                    </span>
                    <button style={enlace("#c73a3a")} onClick={() => quitarEnlace(l)}>Quitar</button>
                  </div>
                ))}
              </>
            )}
            {pestana === "actuaciones" && (
            <>
            <form onSubmit={registrar} style={{ display: "flex", gap: "8px", margin: "14px 0", flexWrap: "wrap" }}>
              <input type="date" max={hoyISO()} value={nueva.fecha} onChange={(e) => setNueva({ ...nueva, fecha: e.target.value })} required style={{ ...inputStyle, width: "150px" }} />
              <input type="text" placeholder="Qué pasó (auto, memorial, notificación...)" value={nueva.descripcion} onChange={(e) => setNueva({ ...nueva, descripcion: e.target.value })} required maxLength={500} style={{ ...inputStyle, flex: 1, minWidth: "180px" }} />
              <button type="submit" style={{ padding: "8px 14px", borderRadius: "8px", border: "none", background: "#0a1a2b", color: "white", cursor: "pointer" }}>Registrar</button>
            </form>
            {errorAct && <p style={mensajeErrorEstilo}>{errorAct}</p>}
            {actuaciones.length === 0 && <p style={{ color: "#6b7f96", fontSize: "13px" }}>Sin actuaciones registradas.</p>}
            {actuaciones.map((a) => (
              <div key={a.id} style={{ display: "flex", justifyContent: "space-between", gap: "10px", padding: "10px 0", borderBottom: "1px dashed #e9edf2", fontSize: "14px" }}>
                <span>
                  <strong>{fecha(a.fecha)}</strong> · {a.descripcion}
                  <div style={{ color: "#6b7f96", fontSize: "12px" }}>Registrada por {a.registrada_por_nombre || "—"}</div>
                </span>
                <button style={enlace("#c73a3a")} onClick={() => borrarActuacion(a)}>Eliminar</button>
              </div>
            ))}
            </>
            )}
          </Modal>
        )}
      </div>
    </Layout>
  );
}
