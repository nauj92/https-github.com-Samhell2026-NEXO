import { useEffect, useState } from "react";
import { ListChecks } from "lucide-react";
import api from "../api";
import Layout from "../components/Layout";
import { mensajeError } from "../utils/errores";
import { fecha } from "../utils/formato";
import {
  Encabezado, Modal, Campo, Dato, Chip, Etiqueta, inputStyle, thStyle, tdStyle, botonPrimario, botonSecundario,
  enlace, mensajeErrorEstilo,
} from "../components/ui";
import { usePermisos } from "../utils/permisos";

const ESTADOS = {
  pendiente: { label: "Pendiente", bg: "#fff3d6", color: "#a8681a" },
  en_curso: { label: "En curso", bg: "#e3effa", color: "#2a6aa8" },
  realizada: { label: "Realizada", bg: "#e2f3e8", color: "#1b8b5e" },
};
const TIPOS = {
  presentar_escrito: "Presentar escrito", retirar_copias: "Retirar copias", notificar: "Notificar",
  diligencia: "Diligencia", redactar: "Redactar borrador", otra: "Otra",
};
const VACIO = { titulo: "", descripcion: "", tipo: "otra", expediente: "", asignado_a: "", fecha_limite: "" };

export default function Tareas() {
  const permiso = usePermisos("tareas");
  const [lista, setLista] = useState([]);
  const [expedientes, setExpedientes] = useState([]);
  const [usuarios, setUsuarios] = useState([]);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(true);
  const [busqueda, setBusqueda] = useState("");
  const [filtro, setFiltro] = useState(null);
  const [form, setForm] = useState(null);
  const [editandoId, setEditandoId] = useState(null);
  const [formError, setFormError] = useState("");
  const [guardando, setGuardando] = useState(false);
  const [detalleId, setDetalleId] = useState(null);
  const [observacion, setObservacion] = useState("");
  const [errorDetalle, setErrorDetalle] = useState("");
  const [subiendo, setSubiendo] = useState(false);

  const cargar = () => {
    setCargando(true);
    api
      .get("/tareas/")
      .then((r) => setLista(r.data))
      .catch((err) => setError(mensajeError(err, "No se pudieron cargar las tareas.")))
      .finally(() => setCargando(false));
  };

  useEffect(() => { cargar(); }, []);
  useEffect(() => {
    if (!permiso.crear) return;
    api.get("/expedientes/").then((r) => setExpedientes(r.data)).catch(() => {});
    api.get("/usuarios/?asignables=1").then((r) => setUsuarios(r.data)).catch(() => {});
  }, [permiso.crear]);

  const detalle = lista.find((t) => t.id === detalleId) || null;
  const abrirDetalle = (t) => { setDetalleId(t.id); setObservacion(t.observacion_cierre || ""); setErrorDetalle(""); };

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const abrirNueva = () => { setForm({ ...VACIO }); setEditandoId(null); setFormError(""); };
  const abrirEditar = (t) => {
    setForm({
      titulo: t.titulo, descripcion: t.descripcion || "", tipo: t.tipo, expediente: t.expediente || "",
      asignado_a: t.asignado_a || "", fecha_limite: t.fecha_limite || "",
    });
    setEditandoId(t.id);
    setFormError("");
  };

  const guardar = async (e) => {
    e.preventDefault();
    setFormError("");
    setGuardando(true);
    try {
      const datos = { ...form };
      ["expediente", "asignado_a", "fecha_limite"].forEach((k) => { if (datos[k] === "") datos[k] = null; });
      if (editandoId) await api.patch(`/tareas/${editandoId}/`, datos);
      else await api.post("/tareas/", datos);
      setForm(null);
      setEditandoId(null);
      cargar();
    } catch (err) {
      setFormError(mensajeError(err, "No se pudo guardar la tarea."));
    } finally {
      setGuardando(false);
    }
  };

  const eliminar = async (t) => {
    if (!window.confirm("¿Eliminar esta tarea? Esta acción no se puede deshacer.")) return;
    try {
      await api.delete(`/tareas/${t.id}/`);
      setDetalleId(null);
      cargar();
    } catch (err) {
      alert(mensajeError(err, "No se pudo eliminar."));
    }
  };

  const cambiarEstado = async (t, estado) => {
    setErrorDetalle("");
    try {
      await api.patch(`/tareas/${t.id}/`, { estado, observacion_cierre: observacion });
      cargar();
    } catch (err) {
      setErrorDetalle(mensajeError(err, "No se pudo actualizar la tarea."));
    }
  };

  const subirComprobante = async (e) => {
    const archivo = e.target.files?.[0];
    e.target.value = "";
    if (!archivo || !detalle) return;
    setErrorDetalle("");
    setSubiendo(true);
    const datos = new FormData();
    datos.append("archivo", archivo);
    try {
      await api.post(`/tareas/${detalle.id}/comprobantes/`, datos);
      cargar();
    } catch (err) {
      setErrorDetalle(mensajeError(err, "No se pudo subir el comprobante."));
    } finally {
      setSubiendo(false);
    }
  };

  const descargar = async (c) => {
    try {
      const r = await api.get(`/tareas/${detalle.id}/comprobantes/${c.id}/`, { responseType: "blob" });
      const url = URL.createObjectURL(r.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = c.nombre;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setErrorDetalle(mensajeError(err, "No se pudo descargar el comprobante."));
    }
  };

  const quitarComprobante = async (c) => {
    if (!window.confirm("¿Eliminar este comprobante?")) return;
    try {
      await api.delete(`/tareas/${detalle.id}/comprobantes/${c.id}/`);
      cargar();
    } catch (err) {
      setErrorDetalle(mensajeError(err, "No se pudo eliminar el comprobante."));
    }
  };

  const conteo = (est) => lista.filter((t) => t.estado === est).length;
  const visibles = lista.filter((t) => {
    const q = busqueda.toLowerCase();
    const coincide = [t.titulo, t.expediente_numero || "", t.asignado_a_nombre || ""].some((x) => x.toLowerCase().includes(q));
    return coincide && (!filtro || t.estado === filtro);
  });
  const vencidas = lista.filter((t) => t.vencida).length;
  const titulo = permiso.crear ? "Tareas" : "Mis tareas";

  return (
    <Layout>
      <div style={{ minHeight: "100vh", background: "#f4f7fb", fontFamily: "sans-serif" }}>
        <Encabezado Icono={ListChecks} titulo={titulo} busqueda={busqueda} setBusqueda={setBusqueda} placeholder="Buscar tarea..." textoBoton="+ Nueva tarea" onNuevo={permiso.crear ? abrirNueva : undefined} />
        <main style={{ padding: "32px" }}>
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
              {vencidas > 0 && (
                <p style={{ background: "#fde8e8", color: "#c73a3a", padding: "10px 14px", borderRadius: "10px", fontSize: "14px" }}>
                  ⚠ {vencidas} tarea(s) con la fecha límite vencida.
                </p>
              )}
              <div style={{ background: "white", borderRadius: "16px", border: "1px solid #eef2f6", overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
                  <thead>
                    <tr style={{ background: "#f8fafc" }}>
                      {["Tarea", "Expediente", "Asignada a", "Fecha límite", "Estado", "Acción"].map((h) => <th key={h} style={thStyle}>{h}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {visibles.map((t) => {
                      const est = ESTADOS[t.estado] || ESTADOS.pendiente;
                      return (
                        <tr key={t.id} style={{ borderTop: "1px solid #f0f3f8" }}>
                          <td style={tdStyle}>
                            <strong>{t.titulo}</strong>
                            <div style={{ color: "#6b7f96", fontSize: "12px" }}>{TIPOS[t.tipo]}</div>
                          </td>
                          <td style={tdStyle}>{t.expediente_numero || "—"}</td>
                          <td style={tdStyle}>{t.asignado_a_nombre || "—"}</td>
                          <td style={{ ...tdStyle, color: t.vencida ? "#c73a3a" : undefined, fontWeight: t.vencida ? 600 : undefined }}>
                            {fecha(t.fecha_limite)}{t.vencida ? " (vencida)" : ""}
                          </td>
                          <td style={tdStyle}><Etiqueta texto={est.label} bg={est.bg} color={est.color} /></td>
                          <td style={tdStyle}>
                            <button style={enlace()} onClick={() => abrirDetalle(t)}>Ver</button>
                            {permiso.crear && <button style={enlace("#a8681a")} onClick={() => abrirEditar(t)}>Editar</button>}
                            {permiso.eliminar && <button style={enlace("#c73a3a")} onClick={() => eliminar(t)}>Eliminar</button>}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                {visibles.length === 0 && (
                  <p style={{ padding: "24px", color: "#6b7f96" }}>{lista.length === 0 ? "No hay tareas por ahora." : "No hay tareas que coincidan."}</p>
                )}
              </div>
            </>
          )}
        </main>

        {form && (
          <Modal onClose={() => setForm(null)} comoFormulario onSubmit={guardar} ancho={560}>
            <h2 style={{ marginTop: 0 }}>{editandoId ? "✏️ Editar tarea" : "+ Nueva tarea"}</h2>
            {formError && <p style={mensajeErrorEstilo}>{formError}</p>}
            <Campo label="Título"><input value={form.titulo} onChange={set("titulo")} required maxLength={200} style={inputStyle} /></Campo>
            <Campo label="Descripción"><textarea value={form.descripcion} onChange={set("descripcion")} rows={3} style={inputStyle} /></Campo>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 14px" }}>
              <Campo label="Tipo">
                <select value={form.tipo} onChange={set("tipo")} style={inputStyle}>
                  {Object.entries(TIPOS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
              </Campo>
              <Campo label="Fecha límite"><input type="date" value={form.fecha_limite} onChange={set("fecha_limite")} style={inputStyle} /></Campo>
              <Campo label="Asignar a">
                <select value={form.asignado_a} onChange={set("asignado_a")} required style={inputStyle}>
                  <option value="">Seleccione...</option>
                  {usuarios.map((u) => <option key={u.id} value={u.id}>{u.nombre_completo}</option>)}
                </select>
              </Campo>
              <Campo label="Expediente (opcional)">
                <select value={form.expediente} onChange={set("expediente")} style={inputStyle}>
                  <option value="">Ninguno</option>
                  {expedientes.map((x) => <option key={x.id} value={x.id}>{x.numero}</option>)}
                </select>
              </Campo>
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "10px" }}>
              <button type="button" style={botonSecundario} onClick={() => setForm(null)}>Cancelar</button>
              <button type="submit" style={botonPrimario} disabled={guardando}>{guardando ? "Guardando..." : "Guardar"}</button>
            </div>
          </Modal>
        )}

        {detalle && (
          <Modal onClose={() => setDetalleId(null)} ancho={600}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h2 style={{ margin: 0, fontSize: "18px" }}>{detalle.titulo}</h2>
              <span onClick={() => setDetalleId(null)} style={{ cursor: "pointer", fontSize: "22px" }}>&times;</span>
            </div>
            {errorDetalle && <p style={mensajeErrorEstilo}>{errorDetalle}</p>}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px", margin: "16px 0" }}>
              <Dato label="Tipo" value={TIPOS[detalle.tipo]} />
              <Dato label="Estado" value={(ESTADOS[detalle.estado] || {}).label} />
              <Dato label="Asignada a" value={detalle.asignado_a_nombre} />
              <Dato label="Creada por" value={detalle.creado_por_nombre} />
              <Dato label="Expediente" value={detalle.expediente_numero} />
              <Dato label="Fecha límite" value={fecha(detalle.fecha_limite)} />
            </div>
            {detalle.descripcion && <Dato label="Descripción" value={<span style={{ whiteSpace: "pre-line" }}>{detalle.descripcion}</span>} />}

            {permiso.editar && (
              <div style={{ marginTop: "16px" }}>
                <Campo label="Observación (qué encontró o resolvió)">
                  <textarea value={observacion} onChange={(e) => setObservacion(e.target.value)} rows={2} style={inputStyle} />
                </Campo>
                <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                  {detalle.estado === "pendiente" && (
                    <button style={botonSecundario} onClick={() => cambiarEstado(detalle, "en_curso")}>Iniciar</button>
                  )}
                  {detalle.estado !== "realizada" && (
                    <button style={botonPrimario} onClick={() => cambiarEstado(detalle, "realizada")}>Marcar como realizada</button>
                  )}
                  {detalle.estado === "realizada" && (
                    <button style={botonSecundario} onClick={() => cambiarEstado(detalle, "en_curso")}>Reabrir</button>
                  )}
                </div>
              </div>
            )}
            {!permiso.editar && detalle.observacion_cierre && <Dato label="Observación" value={detalle.observacion_cierre} />}

            <h3 style={{ fontSize: "15px", marginBottom: "6px" }}>Comprobantes y fotos de cargo</h3>
            {detalle.comprobantes.length === 0 && <p style={{ color: "#6b7f96", fontSize: "13px", margin: "4px 0" }}>Aún no hay comprobantes.</p>}
            {detalle.comprobantes.map((c) => (
              <div key={c.id} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderTop: "1px solid #f0f3f8", fontSize: "14px" }}>
                <span>{c.nombre} <span style={{ color: "#6b7f96", fontSize: "12px" }}>· {c.subido_por_nombre}</span></span>
                <span>
                  <button style={enlace()} onClick={() => descargar(c)}>Descargar</button>
                  {permiso.editar && <button style={enlace("#c73a3a")} onClick={() => quitarComprobante(c)}>Quitar</button>}
                </span>
              </div>
            ))}
            {permiso.editar && (
              <div style={{ marginTop: "10px" }}>
                <input type="file" accept=".pdf,.jpg,.jpeg,.png,.doc,.docx,.xls,.xlsx,.txt" onChange={subirComprobante} disabled={subiendo} />
                {subiendo && <span style={{ marginLeft: "8px", fontSize: "13px" }}>Subiendo...</span>}
              </div>
            )}
          </Modal>
        )}
      </div>
    </Layout>
  );
}
