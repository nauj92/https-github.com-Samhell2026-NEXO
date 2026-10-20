import { useEffect, useState } from "react";
import { CalendarDays, Gavel, Search } from "lucide-react";
import api from "../api";
import { mensajeError } from "../utils/errores";
import Layout from "../components/Layout";

export default function Audiencias() {
  const [audiencias, setAudiencias] = useState([]);
  const [expedientes, setExpedientes] = useState([]);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(true);
  const [mostrarForm, setMostrarForm] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [formError, setFormError] = useState("");
  const [editandoId, setEditandoId] = useState(null);
  const [detalle, setDetalle] = useState(null);
  const [busqueda, setBusqueda] = useState("");

  const [form, setForm] = useState({
    expediente: "",
    fecha_hora: "",
    lugar: "",
    observaciones: "",
  });

  const cargarAudiencias = () => {
    setCargando(true);
    api
      .get("/audiencias/")
      .then((response) => setAudiencias(response.data))
      .catch(() => setError("No se pudieron cargar las audiencias."))
      .finally(() => setCargando(false));
  };

  useEffect(() => {
    cargarAudiencias();
    api.get("/expedientes/").then((response) => setExpedientes(response.data)).catch(() => {});
  }, []);

  const formatFecha = (fechaISO) => {
    const fecha = new Date(fechaISO);
    return fecha.toLocaleString("es-CO", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const esHoy = (fechaISO) => {
    const fecha = new Date(fechaISO);
    const hoy = new Date();
    return (
      fecha.getDate() === hoy.getDate() &&
      fecha.getMonth() === hoy.getMonth() &&
      fecha.getFullYear() === hoy.getFullYear()
    );
  };

  const audienciasFiltradas = audiencias.filter(
    (aud) =>
      aud.expediente_numero.toLowerCase().includes(busqueda.toLowerCase()) ||
      aud.lugar.toLowerCase().includes(busqueda.toLowerCase()) ||
      (aud.expediente_abogado || "").toLowerCase().includes(busqueda.toLowerCase())
  );

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleNuevoClick = () => {
    setForm({ expediente: "", fecha_hora: "", lugar: "", observaciones: "" });
    setEditandoId(null);
    setFormError("");
    setMostrarForm(true);
  };

  const handleEditar = (aud) => {
    setForm({
      expediente: aud.expediente,
      fecha_hora: aud.fecha_hora ? aud.fecha_hora.slice(0, 16) : "",
      lugar: aud.lugar,
      observaciones: aud.observaciones || "",
    });
    setEditandoId(aud.id);
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
        await api.patch(`/audiencias/${editandoId}/`, form);
      } else {
        await api.post("/audiencias/", form);
      }
      setMostrarForm(false);
      setEditandoId(null);
      setForm({ expediente: "", fecha_hora: "", lugar: "", observaciones: "" });
      cargarAudiencias();
    } catch (err) {
      setFormError(mensajeError(err, "No se pudo guardar la audiencia."));
    } finally {
      setGuardando(false);
    }
  };

  const handleEliminar = async (id) => {
    if (!window.confirm("¿Seguro que quieres eliminar esta audiencia?")) return;
    try {
      await api.delete(`/audiencias/${id}/`);
      cargarAudiencias();
    } catch (err) {
      alert(mensajeError(err, "No se pudo eliminar la audiencia."));
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
            <CalendarDays size={22} color="#0a1a2b" />
            Agenda de Audiencias
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
                placeholder="Buscar audiencia..."
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
              + Nueva Audiencia
            </button>
          </div>
        </header>

        <main style={{ padding: "32px" }}>
          {error && <p style={{ color: "#c73a3a" }}>{error}</p>}
          {cargando && <p>Cargando audiencias...</p>}

          {!cargando && !error && (
            <div style={{ background: "white", borderRadius: "16px", border: "1px solid #eef2f6", overflow: "hidden" }}>
              <div style={{ padding: "20px 24px 0" }}>
                <h3 style={{ marginBottom: "16px", color: "#1a2c3e", display: "flex", alignItems: "center", gap: "8px" }}>
                  <CalendarDays size={18} />
                  Próximas Audiencias
                </h3>
              </div>

              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
                <thead>
                  <tr style={{ background: "#f8fafc" }}>
                    <th style={thStyle}>Fecha y Hora</th>
                    <th style={thStyle}>Juzgado</th>
                    <th style={thStyle}>Caso</th>
                    <th style={thStyle}>Abogado</th>
                    <th style={thStyle}>Lugar</th>
                    <th style={thStyle}>Acción</th>
                  </tr>
                </thead>
                <tbody>
                  {audienciasFiltradas.map((aud) => (
                    <tr key={aud.id} style={{ borderTop: "1px solid #f0f3f8" }}>
                      <td style={tdStyle}>
                        <strong>{formatFecha(aud.fecha_hora)}</strong>
                        {esHoy(aud.fecha_hora) && (
                          <span
                            style={{
                              marginLeft: "10px",
                              background: "#fde8e8",
                              color: "#c73a3a",
                              padding: "2px 10px",
                              borderRadius: "30px",
                              fontSize: "11px",
                              fontWeight: 700,
                            }}
                          >
                            Hoy
                          </span>
                        )}
                      </td>
                      <td style={tdStyle}>{aud.expediente_juzgado}</td>
                      <td style={tdStyle}>{aud.expediente_numero}</td>
                      <td style={tdStyle}>
                        <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                          <Gavel size={14} color="#6b7f96" />
                          {aud.expediente_abogado}
                        </span>
                      </td>
                      <td style={tdStyle}>{aud.lugar}</td>
                      <td style={tdStyle}>
                        <span onClick={() => setDetalle(aud)} style={{ color: "#1f3b57", fontWeight: 600, cursor: "pointer", textDecoration: "underline", marginRight: "12px" }}>Ver</span>
                        <span onClick={() => handleEditar(aud)} style={{ color: "#a8681a", fontWeight: 600, cursor: "pointer", textDecoration: "underline", marginRight: "12px" }}>Editar</span>
                        <span onClick={() => handleEliminar(aud.id)} style={{ color: "#c73a3a", fontWeight: 600, cursor: "pointer", textDecoration: "underline" }}>Eliminar</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {audienciasFiltradas.length === 0 && (
                <p style={{ padding: "24px", color: "#6b7f96" }}>No hay audiencias que coincidan.</p>
              )}
            </div>
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
              <h2 style={{ marginBottom: "16px" }}>{editandoId ? "✏️ Editar Audiencia" : "+ Nueva Audiencia"}</h2>
              {formError && <p style={{ color: "#c73a3a", fontSize: "13px", whiteSpace: "pre-line" }}>{formError}</p>}

              <Campo label="Expediente">
                <select name="expediente" value={form.expediente} onChange={handleChange} required style={inputStyle}>
                  <option value="">Selecciona un expediente</option>
                  {expedientes.map((exp) => (
                    <option key={exp.id} value={exp.id}>
                      {exp.numero} — {exp.demandante} vs. {exp.demandado}
                    </option>
                  ))}
                </select>
              </Campo>

              <Campo label="Fecha y hora">
                <input
                  type="datetime-local"
                  name="fecha_hora"
                  value={form.fecha_hora}
                  onChange={handleChange}
                  required
                  style={inputStyle}
                />
              </Campo>

              <Campo label="Lugar">
                <input name="lugar" value={form.lugar} onChange={handleChange} required style={inputStyle} />
              </Campo>

              <Campo label="Observaciones">
                <textarea
                  name="observaciones"
                  value={form.observaciones}
                  onChange={handleChange}
                  style={{ ...inputStyle, minHeight: "70px", resize: "vertical" }}
                />
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
            onClick={() => setDetalle(null)}
          >
            <div
              onClick={(e) => e.stopPropagation()}
              style={{ background: "white", borderRadius: "20px", padding: "28px", width: "420px", maxHeight: "85vh", overflowY: "auto" }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                <h2 style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <CalendarDays size={20} />
                  Detalle de Audiencia
                </h2>
                <span onClick={() => setDetalle(null)} style={{ cursor: "pointer", fontSize: "22px" }}>&times;</span>
              </div>

              <div style={{ display: "grid", gap: "14px" }}>
                <DetalleItem label="Fecha y hora" value={formatFecha(detalle.fecha_hora)} />
                <DetalleItem label="Expediente" value={detalle.expediente_numero} />
                <DetalleItem label="Juzgado" value={detalle.expediente_juzgado} />
                <DetalleItem label="Abogado responsable" value={detalle.expediente_abogado} />
                <DetalleItem label="Lugar" value={detalle.lugar} />
                <DetalleItem label="Observaciones" value={detalle.observaciones || "Sin observaciones."} />
              </div>
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