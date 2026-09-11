import { useEffect, useState } from "react";
import api from "../api";
import Layout from "../components/Layout";
import { FolderOpen } from "lucide-react";


const estadoColors = {
  activo: { bg: "#e2f3e8", color: "#1b8b5e", label: "Activo" },
  tramite: { bg: "#fff3d6", color: "#a8681a", label: "En trámite" },
  cerrado: { bg: "#e9ecf0", color: "#5b6f84", label: "Cerrado" },
};

export default function Expedientes() {
  const [expedientes, setExpedientes] = useState([]);
  const [juzgados, setJuzgados] = useState([]);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(true);
  const [mostrarForm, setMostrarForm] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [formError, setFormError] = useState("");
  const [detalle, setDetalle] = useState(null);
  const [editandoId, setEditandoId] = useState(null);

  const [form, setForm] = useState({
    numero: "",
    juzgado: "",
    demandante: "",
    demandado: "",
    materia: "",
    estado: "activo",
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
  }, []);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleNuevoClick = () => {
    setForm({ numero: "", juzgado: "", demandante: "", demandado: "", materia: "", estado: "activo" });
    setEditandoId(null);
    setFormError("");
    setMostrarForm(true);
  };

  const handleEditar = (exp) => {
    setForm({
      numero: exp.numero,
      juzgado: exp.juzgado,
      demandante: exp.demandante,
      demandado: exp.demandado,
      materia: exp.materia,
      estado: exp.estado,
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
      if (editandoId) {
        await api.patch(`/expedientes/${editandoId}/`, form);
      } else {
        await api.post("/expedientes/", form);
      }
      setMostrarForm(false);
      setEditandoId(null);
      setForm({ numero: "", juzgado: "", demandante: "", demandado: "", materia: "", estado: "activo" });
      cargarExpedientes();
    } catch (err) {
      setFormError("No se pudo guardar el expediente. Revisa que el número no esté repetido.");
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
      alert("No se pudo eliminar el expediente.");
    }
  };

  const [nuevaEtapa, setNuevaEtapa] = useState({ nombre: "", fecha_limite: "" });
  const [guardandoEtapa, setGuardandoEtapa] = useState(false);

  const handleAgregarEtapa = async (e) => {
  e.preventDefault();
  setGuardandoEtapa(true);
  try {
    await api.post("/etapas/", {
      expediente: detalle.id,
      nombre: nuevaEtapa.nombre,
      fecha_limite: nuevaEtapa.fecha_limite || null,
      estado: "pendiente",
      orden: detalle.etapas.length + 1,
    });
    setNuevaEtapa({ nombre: "", fecha_limite: "" });
    // Recarga el expediente actualizado para refrescar el timeline
    const response = await api.get(`/expedientes/${detalle.id}/`);
    setDetalle(response.data);
    cargarExpedientes();
  } catch (err) {
    alert("No se pudo agregar la etapa.");
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
    alert("No se pudo actualizar la etapa.");
  }
 };

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
            }}
          >
            + Nuevo Caso
          </button>
        </header>

        <main style={{ padding: "32px" }}>
          {error && <p style={{ color: "#c73a3a" }}>{error}</p>}
          {cargando && <p>Cargando expedientes...</p>}

          {!cargando && !error && (
            <div style={{ background: "white", borderRadius: "16px", border: "1px solid #eef2f6", overflow: "hidden" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
                <thead>
                  <tr style={{ background: "#f8fafc" }}>
                    <th style={thStyle}>N° Expediente</th>
                    <th style={thStyle}>Demandante</th>
                    <th style={thStyle}>Demandado</th>
                    <th style={thStyle}>Juzgado</th>
                    <th style={thStyle}>Estado</th>
                    <th style={thStyle}>Acción</th>
                  </tr>
                </thead>
                <tbody>
                  {expedientes.map((exp) => {
                    const estado = estadoColors[exp.estado] || estadoColors.activo;
                    return (
                      <tr key={exp.id} style={{ borderTop: "1px solid #f0f3f8" }}>
                        <td style={tdStyle}><strong>{exp.numero}</strong></td>
                        <td style={tdStyle}>{exp.demandante}</td>
                        <td style={tdStyle}>{exp.demandado}</td>
                        <td style={tdStyle}>{exp.juzgado_nombre}</td>
                        <td style={tdStyle}>
                          <span style={{ background: estado.bg, color: estado.color, padding: "4px 12px", borderRadius: "30px", fontSize: "12px", fontWeight: 600 }}>
                            {estado.label}
                          </span>
                        </td>
                        <td style={tdStyle}>
                          <span
                            onClick={() => setDetalle(exp)}
                            style={{ color: "#1f3b57", fontWeight: 600, cursor: "pointer", textDecoration: "underline", marginRight: "12px" }}
                          >
                            Ver
                          </span>
                          <span
                            onClick={() => handleEditar(exp)}
                            style={{ color: "#a8681a", fontWeight: 600, cursor: "pointer", textDecoration: "underline", marginRight: "12px" }}
                          >
                            Editar
                          </span>
                          <span
                            onClick={() => handleEliminar(exp.id)}
                            style={{ color: "#c73a3a", fontWeight: 600, cursor: "pointer", textDecoration: "underline" }}
                          >
                            Eliminar
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              {expedientes.length === 0 && (
                <p style={{ padding: "24px", color: "#6b7f96" }}>No hay expedientes registrados.</p>
              )}
            </div>
          )}
        </main>

        {/* Modal de creación/edición */}
        {mostrarForm && (
          <div
            style={{
              position: "fixed",
              inset: 0,
              background: "rgba(10,26,43,0.5)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              zIndex: 100,
            }}
            onClick={handleCerrarModal}
          >
            <form
              onClick={(e) => e.stopPropagation()}
              onSubmit={handleSubmit}
              style={{
                background: "white",
                borderRadius: "20px",
                padding: "28px",
                width: "420px",
                maxHeight: "85vh",
                overflowY: "auto",
              }}
            >
              <h2 style={{ marginBottom: "16px" }}>{editandoId ? "✏️ Editar Expediente" : "+ Nuevo Expediente"}</h2>
              {formError && <p style={{ color: "#c73a3a", fontSize: "13px" }}>{formError}</p>}

              <Campo label="N° Expediente">
                <input name="numero" value={form.numero} onChange={handleChange} required style={inputStyle} />
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

              <div style={{ display: "flex", gap: "10px", marginTop: "20px" }}>
                <button
                  type="button"
                  onClick={handleCerrarModal}
                  style={{ flex: 1, padding: "10px", borderRadius: "8px", border: "1px solid #d0d9e3", background: "white", cursor: "pointer" }}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={guardando}
                  style={{ flex: 1, padding: "10px", borderRadius: "8px", border: "none", background: "#0a1a2b", color: "white", cursor: "pointer" }}
                >
                  {guardando ? "Guardando..." : "Guardar"}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Modal de detalle */}
        {detalle && (
          <div
            style={{
              position: "fixed",
              inset: 0,
              background: "rgba(10,26,43,0.5)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              zIndex: 100,
            }}
            onClick={() => { setDetalle(null); setNuevaEtapa({ nombre: "", fecha_limite: "" }); }}
          >
            <div
              onClick={(e) => e.stopPropagation()}
              style={{
                background: "white",
                borderRadius: "20px",
                padding: "28px",
                width: "460px",
                maxHeight: "85vh",
                overflowY: "auto",
              }}
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
              <div
                key={etapa.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: "12px",
                  padding: "10px 0",
                  borderBottom: "1px dashed #e9edf2",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                  <span
                    style={{
                      width: "10px",
                      height: "10px",
                      borderRadius: "50%",
                      background: etapa.estado === "completada" ? "#1b8b5e" : etapa.estado === "en_curso" ? "#d4a743" : "#d0d9e3",
                      flexShrink: 0,
                    }}
                  />
                  <span style={{ fontSize: "14px" }}>
                    <strong>{etapa.nombre}</strong>
                    {etapa.fecha_limite && ` · ${etapa.fecha_limite}`}
                  </span>
                </div>
                <select
                  value={etapa.estado}
                  onChange={(e) => handleCambiarEstadoEtapa(etapa.id, e.target.value)}
                  style={{ fontSize: "12px", padding: "3px 6px", borderRadius: "6px", border: "1px solid #d0d9e3" }}
                >
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
                type="date"
                value={nuevaEtapa.fecha_limite}
                onChange={(e) => setNuevaEtapa({ ...nuevaEtapa, fecha_limite: e.target.value })}
                style={{ ...inputStyle, flex: 1 }}
              />
              <button
                type="submit"
                disabled={guardandoEtapa}
                style={{ padding: "8px 14px", borderRadius: "8px", border: "none", background: "#0a1a2b", color: "white", cursor: "pointer", fontSize: "13px" }}
              >
                +
              </button>
            </form>
            </div>
          </div>
        )}
      </div>
    </Layout>
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