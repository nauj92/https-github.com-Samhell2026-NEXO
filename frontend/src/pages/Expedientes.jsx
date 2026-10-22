import { useEffect, useState } from "react";
import { FolderOpen, Scale, Search } from "lucide-react";
import api from "../api";
import { mensajeError } from "../utils/errores";
import Layout from "../components/Layout";

const ESTILO_PLAZO = (dias) =>
  dias == null ? {} : dias < 0 ? { color: "#c73a3a", fontWeight: 700 } : dias <= 3 ? { color: "#a8681a", fontWeight: 700 } : { color: "#1b8b5e" };

function textoPlazo(dias) {
  if (dias == null) return "";
  if (dias < 0) return ` (vencida hace ${-dias} d)`;
  if (dias === 0) return " (vence hoy)";
  return ` (faltan ${dias} d)`;
}

function formatoTamano(b) {
  return b >= 1048576 ? `${(b / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.round(b / 1024))} KB`;
}

const estadoColors = {
  activo: { bg: "#e2f3e8", color: "#1b8b5e", label: "Activo" },
  tramite: { bg: "#fff3d6", color: "#a8681a", label: "En trámite" },
  cerrado: { bg: "#e9ecf0", color: "#5b6f84", label: "Cerrado" },
};

export default function Expedientes() {
  const [expedientes, setExpedientes] = useState([]);
  const [juzgados, setJuzgados] = useState([]);
  const [usuarios, setUsuarios] = useState([]);
  const [clientes, setClientes] = useState([]);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(true);
  const [mostrarForm, setMostrarForm] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [formError, setFormError] = useState("");
  const [detalle, setDetalle] = useState(null);
  const [editandoId, setEditandoId] = useState(null);
  const [busqueda, setBusqueda] = useState("");
  const [filtroEstado, setFiltroEstado] = useState(null);

  const [form, setForm] = useState({
    numero: "",
    juzgado: "",
    cliente: "",
    demandante: "",
    demandado: "",
    materia: "",
    estado: "activo",
    abogado_asignado: "",
  });

  const cargarExpedientes = () => {
    setCargando(true);
    api
      .get("/expedientes/")
      .then((response) => setExpedientes(response.data))
      .catch(() => setError("No se pudieron cargar los expedientes."))
      .finally(() => setCargando(false));
  };

  useEffect(() => {
    cargarExpedientes();
    api.get("/juzgados/").then((response) => setJuzgados(response.data)).catch(() => {});
    api.get("/usuarios/").then((response) => setUsuarios(response.data)).catch(() => {});
    api.get("/clientes/").then((response) => setClientes(response.data)).catch(() => {});
  }, []);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleNuevoClick = () => {
    setForm({ numero: "", juzgado: "", cliente: "", demandante: "", demandado: "", materia: "", estado: "activo", abogado_asignado: "" });
    setEditandoId(null);
    setFormError("");
    setMostrarForm(true);
  };

  const handleEditar = (exp) => {
    setForm({
      numero: exp.numero,
      juzgado: exp.juzgado,
      cliente: exp.cliente || "",
      demandante: exp.demandante,
      demandado: exp.demandado,
      materia: exp.materia,
      estado: exp.estado,
      abogado_asignado: exp.abogado_asignado || "",
    });
    setEditandoId(exp.id);
    setFormError("");
    setMostrarForm(true);
  };

  const handleCerrarModal = () => {
    setMostrarForm(false);
    setEditandoId(null);
    setFormError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError("");
    setGuardando(true);
    try {
      const payload = {
        ...form,
        numero: form.numero.replace(/\D/g, ""),
        cliente: form.cliente || null,
        abogado_asignado: form.abogado_asignado || undefined,
      };
      if (editandoId) {
        await api.patch(`/expedientes/${editandoId}/`, payload);
      } else {
        await api.post("/expedientes/", payload);
      }
      setMostrarForm(false);
      setEditandoId(null);
      setForm({ numero: "", juzgado: "", cliente: "", demandante: "", demandado: "", materia: "", estado: "activo", abogado_asignado: "" });
      cargarExpedientes();
    } catch (err) {
      setFormError(mensajeError(err, "No se pudo guardar el expediente."));
    } finally {
      setGuardando(false);
    }
  };

  const handleEliminar = async (id) => {
    if (!window.confirm("¿Seguro que quieres eliminar este expediente? Esta acción no se puede deshacer.")) {
      return;
    }
    try {
      await api.delete(`/expedientes/${id}/`);
      cargarExpedientes();
    } catch (err) {
      alert(mensajeError(err, "No se pudo eliminar el expediente."));
    }
  };

  const [nuevaEtapa, setNuevaEtapa] = useState({ nombre: "", fecha_limite: "", dias_habiles: "" });
  const [guardandoEtapa, setGuardandoEtapa] = useState(false);

  const handleAgregarEtapa = async (e) => {
    e.preventDefault();
    setGuardandoEtapa(true);
    try {
      const datosEtapa = {
        expediente: detalle.id,
        nombre: nuevaEtapa.nombre,
        estado: "pendiente",
        orden: detalle.etapas.length + 1,
      };
      if (nuevaEtapa.dias_habiles) datosEtapa.dias_habiles = Number(nuevaEtapa.dias_habiles);
      else if (nuevaEtapa.fecha_limite) datosEtapa.fecha_limite = nuevaEtapa.fecha_limite;
      await api.post("/etapas/", datosEtapa);
      setNuevaEtapa({ nombre: "", fecha_limite: "", dias_habiles: "" });
      const response = await api.get(`/expedientes/${detalle.id}/`);
      setDetalle(response.data);
      cargarExpedientes();
    } catch (err) {
      alert(mensajeError(err, "No se pudo agregar la etapa."));
    } finally {
      setGuardandoEtapa(false);
    }
  };

  const handleCambiarEstadoEtapa = async (etapaId, nuevoEstado) => {
    try {
      await api.patch(`/etapas/${etapaId}/`, { estado: nuevoEstado });
      const response = await api.get(`/expedientes/${detalle.id}/`);
      setDetalle(response.data);
      cargarExpedientes();
    } catch (err) {
      alert(mensajeError(err, "No se pudo actualizar la etapa."));
    }
  };

  const [documentos, setDocumentos] = useState([]);
  const [historial, setHistorial] = useState([]);
  const [subiendo, setSubiendo] = useState(false);
  const [errorDoc, setErrorDoc] = useState("");

  const abrirDetalle = (exp) => {
    setDetalle(exp);
    setDocumentos([]);
    setHistorial([]);
    setErrorDoc("");
    api.get(`/expedientes/${exp.id}/documentos/`).then((r) => setDocumentos(r.data)).catch(() => {});
    api.get(`/expedientes/${exp.id}/historial/`).then((r) => setHistorial(r.data)).catch(() => {});
  };

  const handleSubirDocumento = async (e) => {
    const archivo = e.target.files?.[0];
    e.target.value = "";
    if (!archivo) return;
    setErrorDoc("");
    if (archivo.size > 5 * 1024 * 1024) {
      setErrorDoc("El archivo supera el tamaño máximo permitido (5 MB).");
      return;
    }
    const fd = new FormData();
    fd.append("archivo", archivo);
    setSubiendo(true);
    try {
      await api.post(`/expedientes/${detalle.id}/documentos/`, fd);
      const r = await api.get(`/expedientes/${detalle.id}/documentos/`);
      setDocumentos(r.data);
    } catch (err) {
      setErrorDoc(mensajeError(err, "No se pudo subir el archivo."));
    } finally {
      setSubiendo(false);
    }
  };

  const handleDescargarDocumento = async (doc) => {
    try {
      const r = await api.get(`/expedientes/${detalle.id}/documento/${doc.id}/`, { responseType: "blob" });
      const url = URL.createObjectURL(r.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = doc.nombre;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setErrorDoc(mensajeError(err, "No se pudo descargar el archivo."));
    }
  };

  const handleEliminarDocumento = async (doc) => {
    if (!window.confirm(`¿Eliminar el documento "${doc.nombre}"?`)) return;
    try {
      await api.delete(`/expedientes/${detalle.id}/documento/${doc.id}/`);
      setDocumentos((prev) => prev.filter((d) => d.id !== doc.id));
      api.get(`/expedientes/${detalle.id}/historial/`).then((r) => setHistorial(r.data)).catch(() => {});
    } catch (err) {
      setErrorDoc(mensajeError(err, "No se pudo eliminar el archivo."));
    }
  };

  const conteoEstados = {
    activo: expedientes.filter((e) => e.estado === "activo").length,
    tramite: expedientes.filter((e) => e.estado === "tramite").length,
    cerrado: expedientes.filter((e) => e.estado === "cerrado").length,
  };

  const expedientesFiltrados = expedientes.filter((exp) => {
    const coincideBusqueda =
      exp.numero.toLowerCase().includes(busqueda.toLowerCase()) ||
      exp.demandante.toLowerCase().includes(busqueda.toLowerCase()) ||
      exp.demandado.toLowerCase().includes(busqueda.toLowerCase());
    const coincideEstado = !filtroEstado || exp.estado === filtroEstado;
    return coincideBusqueda && coincideEstado;
  });

  return (
    <Layout>
      <div style={{ minHeight: "100vh", background: "#f4f7fb", fontFamily: "sans-serif" }}>
        <header
          style={{
            background: "white",
            padding: "16px 32px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            borderBottom: "1px solid #e9edf2",
          }}
        >
          <div style={{ fontSize: "20px", fontWeight: "bold", display: "flex", alignItems: "center", gap: "10px" }}>
            <FolderOpen size={22} color="#0a1a2b" />
            Expedientes Judiciales
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <div
              style={{
                background: "#f4f7fb",
                padding: "8px 16px",
                borderRadius: "30px",
                display: "flex",
                alignItems: "center",
                gap: "10px",
                border: "1px solid #e9edf2",
                width: "220px",
              }}
            >
              <Search size={16} color="#8899b4" />
              <input
                type="text"
                placeholder="Buscar expediente..."
                value={busqueda}
                onChange={(e) => setBusqueda(e.target.value)}
                style={{ border: "none", background: "transparent", outline: "none", fontSize: "14px", width: "100%" }}
              />
            </div>

            <button
              onClick={handleNuevoClick}
              style={{
                background: "#0a1a2b",
                color: "white",
                border: "none",
                padding: "10px 20px",
                borderRadius: "30px",
                cursor: "pointer",
                fontWeight: 600,
                whiteSpace: "nowrap",
              }}
            >
              + Nuevo Caso
            </button>
          </div>
        </header>

        <main style={{ padding: "32px" }}>
          {error && <p style={{ color: "#c73a3a" }}>{error}</p>}
          {cargando && <p>Cargando expedientes...</p>}

          {!cargando && !error && (
            <>
              <div style={{ display: "flex", gap: "10px", marginBottom: "20px", flexWrap: "wrap" }}>
                <FiltroBadge label={`Todos (${expedientes.length})`} activo={filtroEstado === null} onClick={() => setFiltroEstado(null)} bg="#eef2f6" color="#1a2c3e" />
                <FiltroBadge label={`Activos (${conteoEstados.activo})`} activo={filtroEstado === "activo"} onClick={() => setFiltroEstado("activo")} bg="#e2f3e8" color="#1b8b5e" />
                <FiltroBadge label={`En trámite (${conteoEstados.tramite})`} activo={filtroEstado === "tramite"} onClick={() => setFiltroEstado("tramite")} bg="#fff3d6" color="#a8681a" />
                <FiltroBadge label={`Cerrados (${conteoEstados.cerrado})`} activo={filtroEstado === "cerrado"} onClick={() => setFiltroEstado("cerrado")} bg="#e9ecf0" color="#5b6f84" />
              </div>

              <div style={{ background: "white", borderRadius: "16px", border: "1px solid #eef2f6", overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
                  <thead>
                    <tr style={{ background: "#f8fafc" }}>
                      <th style={thStyle}>N° Expediente</th>
                      <th style={thStyle}>Cliente</th>
                      <th style={thStyle}>Demandante</th>
                      <th style={thStyle}>Demandado</th>
                      <th style={thStyle}>Juzgado</th>
                      <th style={thStyle}>Estado</th>
                      <th style={thStyle}>Abogado</th>
                      <th style={thStyle}>Acción</th>
                    </tr>
                  </thead>
                  <tbody>
                    {expedientesFiltrados.map((exp) => {
                      const estado = estadoColors[exp.estado] || estadoColors.activo;
                      return (
                        <tr key={exp.id} style={{ borderTop: "1px solid #f0f3f8" }}>
                          <td style={tdStyle}><strong>{exp.numero}</strong></td>
                          <td style={tdStyle}>{exp.cliente_nombre || "Sin cliente"}</td>
                          <td style={tdStyle}>{exp.demandante}</td>
                          <td style={tdStyle}>{exp.demandado}</td>
                          <td style={tdStyle}>{exp.juzgado_nombre}</td>
                          <td style={tdStyle}>
                            <span style={{ background: estado.bg, color: estado.color, padding: "4px 12px", borderRadius: "30px", fontSize: "12px", fontWeight: 600 }}>
                              {estado.label}
                            </span>
                          </td>
                          <td style={tdStyle}>{exp.abogado_asignado_nombre || "Sin asignar"}</td>
                          <td style={tdStyle}>
                            <span onClick={() => abrirDetalle(exp)} style={{ color: "#1f3b57", fontWeight: 600, cursor: "pointer", textDecoration: "underline", marginRight: "12px" }}>Ver</span>
                            <span onClick={() => handleEditar(exp)} style={{ color: "#a8681a", fontWeight: 600, cursor: "pointer", textDecoration: "underline", marginRight: "12px" }}>Editar</span>
                            <span onClick={() => handleEliminar(exp.id)} style={{ color: "#c73a3a", fontWeight: 600, cursor: "pointer", textDecoration: "underline" }}>Eliminar</span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                {expedientesFiltrados.length === 0 && (
                  <p style={{ padding: "24px", color: "#6b7f96" }}>No hay expedientes que coincidan.</p>
                )}
              </div>
            </>
          )}
        </main>

        {mostrarForm && (
          <div
            style={{ position: "fixed", inset: 0, background: "rgba(10,26,43,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100 }}
            onClick={handleCerrarModal}
          >
            <form
              onClick={(e) => e.stopPropagation()}
              onSubmit={handleSubmit}
              style={{ background: "white", borderRadius: "20px", padding: "28px", width: "420px", maxHeight: "85vh", overflowY: "auto" }}
            >
              <h2 style={{ marginBottom: "16px" }}>{editandoId ? "✏️ Editar Expediente" : "+ Nuevo Expediente"}</h2>
              {formError && <p style={{ color: "#c73a3a", fontSize: "13px", whiteSpace: "pre-line" }}>{formError}</p>}

              <Campo label="N° Expediente">
                <input
                  name="numero"
                  value={form.numero}
                  onChange={handleChange}
                  required
                  inputMode="numeric"
                  placeholder="23 dígitos, ej. 11001310301220250012300"
                  style={inputStyle}
                />
                <small style={{ color: form.numero.replace(/\D/g, "").length === 23 ? "#1b8b5e" : "#6b7f96" }}>
                  {form.numero.replace(/\D/g, "").length}/23 dígitos (radicado: ciudad, corporación, especialidad, despacho, año, consecutivo, recurso)
                </small>
              </Campo>

              <Campo label="Cliente (a quién representa el despacho)">
                <select name="cliente" value={form.cliente} onChange={handleChange} style={inputStyle}>
                  <option value="">Sin cliente asignado</option>
                  {clientes.map((c) => (
                    <option key={c.id} value={c.id}>{c.nombre}</option>
                  ))}
                </select>
              </Campo>

              <Campo label="Juzgado">
                <select name="juzgado" value={form.juzgado} onChange={handleChange} required style={inputStyle}>
                  <option value="">Selecciona un juzgado</option>
                  {juzgados.map((j) => (
                    <option key={j.id} value={j.id}>{j.nombre}</option>
                  ))}
                </select>
              </Campo>

              <Campo label="Demandante">
                <input name="demandante" value={form.demandante} onChange={handleChange} required style={inputStyle} />
              </Campo>

              <Campo label="Demandado">
                <input name="demandado" value={form.demandado} onChange={handleChange} required style={inputStyle} />
              </Campo>

              <Campo label="Materia">
                <input name="materia" value={form.materia} onChange={handleChange} required style={inputStyle} />
              </Campo>

              <Campo label="Estado">
                <select name="estado" value={form.estado} onChange={handleChange} style={inputStyle}>
                  <option value="activo">Activo</option>
                  <option value="tramite">En trámite</option>
                  <option value="cerrado">Cerrado</option>
                </select>
              </Campo>

              <Campo label="Abogado Asignado">
                <select name="abogado_asignado" value={form.abogado_asignado} onChange={handleChange} style={inputStyle}>
                  <option value="">Sin asignar (se asigna a ti por defecto)</option>
                  {usuarios.map((u) => (
                    <option key={u.id} value={u.id}>{u.nombre_completo}</option>
                  ))}
                </select>
              </Campo>

              <div style={{ display: "flex", gap: "10px", marginTop: "20px" }}>
                <button type="button" onClick={handleCerrarModal} style={{ flex: 1, padding: "10px", borderRadius: "8px", border: "1px solid #d0d9e3", background: "white", cursor: "pointer" }}>
                  Cancelar
                </button>
                <button type="submit" disabled={guardando} style={{ flex: 1, padding: "10px", borderRadius: "8px", border: "none", background: "#0a1a2b", color: "white", cursor: "pointer" }}>
                  {guardando ? "Guardando..." : "Guardar"}
                </button>
              </div>
            </form>
          </div>
        )}

        {detalle && (
          <div
            style={{ position: "fixed", inset: 0, background: "rgba(10,26,43,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100 }}
            onClick={() => { setDetalle(null); setNuevaEtapa({ nombre: "", fecha_limite: "", dias_habiles: "" }); }}
          >
            <div
              onClick={(e) => e.stopPropagation()}
              style={{ background: "white", borderRadius: "20px", padding: "28px", width: "560px", maxWidth: "95vw", maxHeight: "88vh", overflowY: "auto" }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                <h2 style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <Scale size={20} />
                  Expediente {detalle.numero}
                </h2>
                <span onClick={() => setDetalle(null)} style={{ cursor: "pointer", fontSize: "22px" }}>&times;</span>
              </div>

              <p>
                <span style={{
                  background: (estadoColors[detalle.estado] || estadoColors.activo).bg,
                  color: (estadoColors[detalle.estado] || estadoColors.activo).color,
                  padding: "4px 12px", borderRadius: "30px", fontSize: "12px", fontWeight: 600,
                }}>
                  {(estadoColors[detalle.estado] || estadoColors.activo).label}
                </span>
              </p>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px", margin: "16px 0" }}>
                <DetalleItem label="Cliente" value={detalle.cliente_nombre || "Sin cliente asignado"} />
                <DetalleItem label="Juzgado" value={detalle.juzgado_nombre} />
                <DetalleItem label="Demandante" value={detalle.demandante} />
                <DetalleItem label="Demandado" value={detalle.demandado} />
                <DetalleItem label="Materia" value={detalle.materia} />
                <DetalleItem label="Abogado Asignado" value={detalle.abogado_asignado_nombre || "Sin asignar"} />
              </div>

              <h4 style={{ marginTop: "20px", marginBottom: "12px" }}>📌 Etapas del Proceso</h4>
              {detalle.etapas.length === 0 && (
                <p style={{ color: "#6b7f96", fontSize: "13px" }}>Sin etapas registradas aún.</p>
              )}
              {detalle.etapas.map((etapa) => (
                <div key={etapa.id} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "12px", padding: "10px 0", borderBottom: "1px dashed #e9edf2" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <span style={{
                      width: "10px", height: "10px", borderRadius: "50%",
                      background: etapa.estado === "completada" ? "#1b8b5e" : etapa.estado === "en_curso" ? "#d4a743" : "#d0d9e3",
                      flexShrink: 0,
                    }} />
                    <span style={{ fontSize: "14px" }}>
                      <strong>{etapa.nombre}</strong>
                      {etapa.fecha_limite && ` · ${etapa.fecha_limite}`}
                      {etapa.fecha_limite && etapa.estado !== "completada" && (
                        <span style={{ fontSize: "12px", ...ESTILO_PLAZO(etapa.dias_restantes) }}>{textoPlazo(etapa.dias_restantes)}</span>
                      )}
                    </span>
                  </div>
                  <select value={etapa.estado} onChange={(e) => handleCambiarEstadoEtapa(etapa.id, e.target.value)} style={{ fontSize: "12px", padding: "3px 6px", borderRadius: "6px", border: "1px solid #d0d9e3" }}>
                    <option value="pendiente">Pendiente</option>
                    <option value="en_curso">En curso</option>
                    <option value="completada">Completada</option>
                  </select>
                </div>
              ))}

              <form onSubmit={handleAgregarEtapa} style={{ display: "flex", gap: "8px", marginTop: "14px" }}>
                <input
                  type="text"
                  placeholder="Nombre de la etapa"
                  value={nuevaEtapa.nombre}
                  onChange={(e) => setNuevaEtapa({ ...nuevaEtapa, nombre: e.target.value })}
                  required
                  style={{ ...inputStyle, flex: 2 }}
                />
                <input
                  type="number"
                  min="1"
                  max="365"
                  placeholder="Días háb."
                  title="Días hábiles desde hoy (excluye fines de semana y festivos de Colombia)"
                  value={nuevaEtapa.dias_habiles}
                  onChange={(e) => setNuevaEtapa({ ...nuevaEtapa, dias_habiles: e.target.value, fecha_limite: "" })}
                  style={{ ...inputStyle, flex: 1, minWidth: 0 }}
                />
                <input
                  type="date"
                  title="O indique la fecha límite directamente"
                  value={nuevaEtapa.fecha_limite}
                  disabled={!!nuevaEtapa.dias_habiles}
                  onChange={(e) => setNuevaEtapa({ ...nuevaEtapa, fecha_limite: e.target.value })}
                  style={{ ...inputStyle, flex: 1, minWidth: 0 }}
                />
                <button type="submit" disabled={guardandoEtapa} style={{ padding: "8px 14px", borderRadius: "8px", border: "none", background: "#0a1a2b", color: "white", cursor: "pointer", fontSize: "13px" }}>
                  +
                </button>
              </form>
              <p style={{ fontSize: "11px", color: "#6b7f96", marginTop: "6px" }}>
                Los días hábiles excluyen sábados, domingos y festivos de Colombia. No considera vacancia judicial ni suspensiones de términos: verifique siempre el plazo con el despacho.
              </p>

              <h4 style={{ marginTop: "24px", marginBottom: "10px" }}>📎 Documentos</h4>
              {errorDoc && <p style={{ color: "#c73a3a", fontSize: "13px", whiteSpace: "pre-line" }}>{errorDoc}</p>}
              {documentos.length === 0 && <p style={{ color: "#6b7f96", fontSize: "13px" }}>Sin documentos adjuntos.</p>}
              {documentos.map((d) => (
                <div key={d.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 0", borderBottom: "1px dashed #e9edf2", fontSize: "13px", gap: "8px" }}>
                  <span style={{ overflow: "hidden", textOverflow: "ellipsis" }}>
                    <strong>{d.nombre}</strong> · {formatoTamano(d.tamano)}
                    <br />
                    <span style={{ color: "#6b7f96" }}>
                      {d.subido_por_nombre || "—"} · {new Date(d.subido_en).toLocaleString("es-CO")}
                    </span>
                  </span>
                  <span style={{ display: "flex", gap: "6px", flexShrink: 0 }}>
                    <button type="button" onClick={() => handleDescargarDocumento(d)} style={{ padding: "4px 10px", borderRadius: "6px", border: "1px solid #d0d9e3", background: "white", cursor: "pointer" }}>Descargar</button>
                    <button type="button" onClick={() => handleEliminarDocumento(d)} style={{ padding: "4px 10px", borderRadius: "6px", border: "none", background: "#fde8e8", color: "#c73a3a", cursor: "pointer" }}>Eliminar</button>
                  </span>
                </div>
              ))}
              <label style={{ display: "inline-block", marginTop: "10px", padding: "8px 14px", borderRadius: "8px", background: "#0a1a2b", color: "white", cursor: "pointer", fontSize: "13px", opacity: subiendo ? 0.6 : 1 }}>
                {subiendo ? "Subiendo..." : "+ Adjuntar documento"}
                <input type="file" onChange={handleSubirDocumento} disabled={subiendo} style={{ display: "none" }} accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.txt" />
              </label>
              <p style={{ fontSize: "11px", color: "#6b7f96" }}>PDF, Word, Excel, imágenes o texto. Máximo 5 MB.</p>

              <h4 style={{ marginTop: "24px", marginBottom: "10px" }}>🕑 Historial de cambios</h4>
              {historial.length === 0 && <p style={{ color: "#6b7f96", fontSize: "13px" }}>Sin cambios registrados.</p>}
              {historial.map((h, i) => (
                <div key={i} style={{ padding: "8px 0", borderBottom: "1px dashed #e9edf2", fontSize: "13px" }}>
                  <strong>{h.tipo}</strong> · {h.usuario || "Sistema"} ·{" "}
                  <span style={{ color: "#6b7f96" }}>{new Date(h.fecha).toLocaleString("es-CO")}</span>
                  {(h.cambios || []).map((c, j) => (
                    <div key={j} style={{ marginLeft: "12px", color: "#4a5a70" }}>
                      {c.campo}: <s>{String(c.anterior ?? "—")}</s> → <strong>{String(c.nuevo ?? "—")}</strong>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}

function FiltroBadge({ label, activo, onClick, bg, color }) {
  return (
    <span onClick={onClick} style={{ background: bg, color, padding: "6px 16px", borderRadius: "30px", fontSize: "13px", fontWeight: 600, cursor: "pointer", border: activo ? `2px solid ${color}` : "2px solid transparent" }}>
      {label}
    </span>
  );
}

function DetalleItem({ label, value }) {
  return (
    <div>
      <div style={{ fontSize: "11px", color: "#6b7f96", textTransform: "uppercase", letterSpacing: "0.5px" }}>{label}</div>
      <div style={{ fontWeight: 500, marginTop: "2px" }}>{value}</div>
    </div>
  );
}

function Campo({ label, children }) {
  return (
    <div style={{ marginBottom: "14px" }}>
      <label style={{ fontSize: "13px", color: "#6b7f96", display: "block", marginBottom: "4px" }}>{label}</label>
      {children}
    </div>
  );
}

const inputStyle = {
  width: "100%",
  padding: "8px 10px",
  borderRadius: "8px",
  border: "1px solid #d0d9e3",
  fontSize: "14px",
  boxSizing: "border-box",
};

const thStyle = { textAlign: "left", padding: "14px 16px", color: "#6b7f96", fontWeight: 600, borderBottom: "1px solid #e9edf2" };
const tdStyle = { padding: "14px 16px" };