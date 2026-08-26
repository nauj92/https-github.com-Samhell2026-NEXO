import { useEffect, useState } from "react";
import api from "../api";
import Layout from "../components/Layout";

const estadoColors = {
  pendiente: { bg: "#fff3d6", color: "#a8681a", label: "Pendiente" },
  pagada: { bg: "#e2f3e8", color: "#1b8b5e", label: "Pagada" },
  vencida: { bg: "#fde8e8", color: "#c73a3a", label: "Vencida" },
  anulada: { bg: "#e9ecf0", color: "#5b6f84", label: "Anulada" },
};

export default function Facturacion() {
  const [facturas, setFacturas] = useState([]);
  const [expedientes, setExpedientes] = useState([]);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(true);
  const [mostrarForm, setMostrarForm] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [formError, setFormError] = useState("");
  const [editandoId, setEditandoId] = useState(null);

  const [form, setForm] = useState({
    numero: "",
    expediente: "",
    cliente: "",
    concepto: "",
    monto: "",
    estado: "pendiente",
    fecha_vencimiento: "",
  });

  const cargarFacturas = () => {
    setCargando(true);
    api
      .get("/facturas/")
      .then((response) => setFacturas(response.data))
      .catch(() => setError("No se pudieron cargar las facturas."))
      .finally(() => setCargando(false));
  };

  useEffect(() => {
    cargarFacturas();
    api.get("/expedientes/").then((response) => setExpedientes(response.data)).catch(() => {});
  }, []);

  const formatMonto = (monto) =>
    new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(monto);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleNuevoClick = () => {
    setForm({ numero: "", expediente: "", cliente: "", concepto: "", monto: "", estado: "pendiente", fecha_vencimiento: "" });
    setEditandoId(null);
    setFormError("");
    setMostrarForm(true);
  };

  const handleEditar = (fac) => {
    setForm({
      numero: fac.numero,
      expediente: fac.expediente || "",
      cliente: fac.cliente,
      concepto: fac.concepto,
      monto: fac.monto,
      estado: fac.estado,
      fecha_vencimiento: fac.fecha_vencimiento || "",
    });
    setEditandoId(fac.id);
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
      const payload = { ...form, expediente: form.expediente || null };
      if (editandoId) {
        await api.patch(`/facturas/${editandoId}/`, payload);
      } else {
        await api.post("/facturas/", payload);
      }
      setMostrarForm(false);
      setEditandoId(null);
      setForm({ numero: "", expediente: "", cliente: "", concepto: "", monto: "", estado: "pendiente", fecha_vencimiento: "" });
      cargarFacturas();
    } catch (err) {
      setFormError("No se pudo guardar la factura. Revisa que el número no esté repetido.");
    } finally {
      setGuardando(false);
    }
  };

  const handleEliminar = async (id) => {
    if (!window.confirm("¿Seguro que quieres eliminar esta factura?")) return;
    try {
      await api.delete(`/facturas/${id}/`);
      cargarFacturas();
    } catch (err) {
      alert("No se pudo eliminar la factura.");
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
          <div style={{ fontSize: "20px", fontWeight: "bold" }}>💰 Facturación</div>
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
            + Nueva Factura
          </button>
        </header>

        <main style={{ padding: "32px" }}>
          {error && <p style={{ color: "#c73a3a" }}>{error}</p>}
          {cargando && <p>Cargando facturas...</p>}

          {!cargando && !error && (
            <div style={{ background: "white", borderRadius: "16px", border: "1px solid #eef2f6", overflow: "hidden" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
                <thead>
                  <tr style={{ background: "#f8fafc" }}>
                    <th style={thStyle}>N° Factura</th>
                    <th style={thStyle}>Cliente</th>
                    <th style={thStyle}>Concepto</th>
                    <th style={thStyle}>Monto</th>
                    <th style={thStyle}>Estado</th>
                    <th style={thStyle}>Vencimiento</th>
                    <th style={thStyle}>Acción</th>
                  </tr>
                </thead>
                <tbody>
                  {facturas.map((fac) => {
                    const estado = estadoColors[fac.estado] || estadoColors.pendiente;
                    return (
                      <tr key={fac.id} style={{ borderTop: "1px solid #f0f3f8" }}>
                        <td style={tdStyle}><strong>{fac.numero}</strong></td>
                        <td style={tdStyle}>{fac.cliente}</td>
                        <td style={tdStyle}>{fac.concepto}</td>
                        <td style={tdStyle}>{formatMonto(fac.monto)}</td>
                        <td style={tdStyle}>
                          <span style={{ background: estado.bg, color: estado.color, padding: "4px 12px", borderRadius: "30px", fontSize: "12px", fontWeight: 600 }}>
                            {estado.label}
                          </span>
                        </td>
                        <td style={tdStyle}>{fac.fecha_vencimiento || "—"}</td>
                        <td style={tdStyle}>
                          <span
                            onClick={() => handleEditar(fac)}
                            style={{ color: "#a8681a", fontWeight: 600, cursor: "pointer", textDecoration: "underline", marginRight: "12px" }}
                          >
                            Editar
                          </span>
                          <span
                            onClick={() => handleEliminar(fac.id)}
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
              {facturas.length === 0 && (
                <p style={{ padding: "24px", color: "#6b7f96" }}>No hay facturas registradas.</p>
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
              <h2 style={{ marginBottom: "16px" }}>{editandoId ? "✏️ Editar Factura" : "+ Nueva Factura"}</h2>
              {formError && <p style={{ color: "#c73a3a", fontSize: "13px" }}>{formError}</p>}

              <Campo label="N° Factura">
                <input name="numero" value={form.numero} onChange={handleChange} required style={inputStyle} />
              </Campo>

              <Campo label="Expediente (opcional)">
                <select name="expediente" value={form.expediente} onChange={handleChange} style={inputStyle}>
                  <option value="">Sin expediente asociado</option>
                  {expedientes.map((exp) => (
                    <option key={exp.id} value={exp.id}>{exp.numero}</option>
                  ))}
                </select>
              </Campo>

              <Campo label="Cliente">
                <input name="cliente" value={form.cliente} onChange={handleChange} required style={inputStyle} />
              </Campo>

              <Campo label="Concepto">
                <input name="concepto" value={form.concepto} onChange={handleChange} required style={inputStyle} />
              </Campo>

              <Campo label="Monto">
                <input type="number" name="monto" value={form.monto} onChange={handleChange} required style={inputStyle} />
              </Campo>

              <Campo label="Estado">
                <select name="estado" value={form.estado} onChange={handleChange} style={inputStyle}>
                  <option value="pendiente">Pendiente</option>
                  <option value="pagada">Pagada</option>
                  <option value="vencida">Vencida</option>
                  <option value="anulada">Anulada</option>
                </select>
              </Campo>

              <Campo label="Fecha de vencimiento">
                <input type="date" name="fecha_vencimiento" value={form.fecha_vencimiento} onChange={handleChange} style={inputStyle} />
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
      </div>
    </Layout>
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