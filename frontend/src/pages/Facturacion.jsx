import { useEffect, useState } from "react";
import { Wallet, Receipt, Search } from "lucide-react";
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
  const [clientes, setClientes] = useState([]);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(true);
  const [mostrarForm, setMostrarForm] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [formError, setFormError] = useState("");
  const [editandoId, setEditandoId] = useState(null);
  const [detalle, setDetalle] = useState(null);
  const [busqueda, setBusqueda] = useState("");

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
    api.get("/clientes/").then((response) => setClientes(response.data)).catch(() => {});
  }, []);

  const formatMonto = (monto) =>
    new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(monto);

  const facturasFiltradas = facturas.filter(
    (fac) =>
      fac.numero.toLowerCase().includes(busqueda.toLowerCase()) ||
      (fac.cliente_nombre || "").toLowerCase().includes(busqueda.toLowerCase()) ||
      fac.concepto.toLowerCase().includes(busqueda.toLowerCase())
  );

  const totales = {
    pendiente: facturas.filter((f) => f.estado === "pendiente").reduce((sum, f) => sum + Number(f.monto), 0),
    pagada: facturas.filter((f) => f.estado === "pagada").reduce((sum, f) => sum + Number(f.monto), 0),
    vencida: facturas.filter((f) => f.estado === "vencida").reduce((sum, f) => sum + Number(f.monto), 0),
  };

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
      cliente: fac.cliente || "",
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
      const payload = { ...form, expediente: form.expediente || null, cliente: form.cliente || null };
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
          <div style={{ fontSize: "20px", fontWeight: "bold", display: "flex", alignItems: "center", gap: "10px" }}>
            <Wallet size={22} color="#0a1a2b" />
            Facturación
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
                placeholder="Buscar factura..."
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
              + Nueva Factura
            </button>
          </div>
        </header>

        <main style={{ padding: "32px" }}>
          {error && <p style={{ color: "#c73a3a" }}>{error}</p>}
          {cargando && <p>Cargando facturas...</p>}

          {!cargando && !error && (
            <>
              {/* Tarjetas de resumen */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(3, 1fr)",
                  gap: "24px",
                  marginBottom: "24px",
                }}
              >
                <TarjetaResumen label="Total Pendiente" valor={formatMonto(totales.pendiente)} color="#a8681a" />
                <TarjetaResumen label="Total Pagado" valor={formatMonto(totales.pagada)} color="#1b8b5e" />
                <TarjetaResumen label="Total Vencido" valor={formatMonto(totales.vencida)} color="#c73a3a" />
              </div>

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
                    {facturasFiltradas.map((fac) => {
                      const estado = estadoColors[fac.estado] || estadoColors.pendiente;
                      return (
                        <tr key={fac.id} style={{ borderTop: "1px solid #f0f3f8" }}>
                          <td style={tdStyle}><strong>{fac.numero}</strong></td>
                          <td style={tdStyle}>{fac.cliente_nombre || "Sin cliente"}</td>
                          <td style={tdStyle}>{fac.concepto}</td>
                          <td style={tdStyle}>{formatMonto(fac.monto)}</td>
                          <td style={tdStyle}>
                            <span style={{ background: estado.bg, color: estado.color, padding: "4px 12px", borderRadius: "30px", fontSize: "12px", fontWeight: 600 }}>
                              {estado.label}
                            </span>
                          </td>
                          <td style={tdStyle}>{fac.fecha_vencimiento || "—"}</td>
                          <td style={tdStyle}>
                            <span onClick={() => setDetalle(fac)} style={{ color: "#1f3b57", fontWeight: 600, cursor: "pointer", textDecoration: "underline", marginRight: "12px" }}>Ver</span>
                            <span onClick={() => handleEditar(fac)} style={{ color: "#a8681a", fontWeight: 600, cursor: "pointer", textDecoration: "underline", marginRight: "12px" }}>Editar</span>
                            <span onClick={() => handleEliminar(fac.id)} style={{ color: "#c73a3a", fontWeight: 600, cursor: "pointer", textDecoration: "underline" }}>Eliminar</span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                {facturasFiltradas.length === 0 && (
                  <p style={{ padding: "24px", color: "#6b7f96" }}>No hay facturas que coincidan.</p>
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
              <h2 style={{ marginBottom: "16px" }}>{editandoId ? "✏️ Editar Factura" : "+ Nueva Factura"}</h2>
              {formError && <p style={{ color: "#c73a3a", fontSize: "13px" }}>{formError}</p>}

              <Campo label="N° Factura">
                <input name="numero" value={form.numero} onChange={handleChange} required style={inputStyle} />
              </Campo>

              <Campo label="Cliente">
                <select name="cliente" value={form.cliente} onChange={handleChange} style={inputStyle}>
                  <option value="">Sin cliente asignado</option>
                  {clientes.map((c) => (
                    <option key={c.id} value={c.id}>{c.nombre}</option>
                  ))}
                </select>
              </Campo>

              <Campo label="Expediente (opcional)">
                <select name="expediente" value={form.expediente} onChange={handleChange} style={inputStyle}>
                  <option value="">Sin expediente asociado</option>
                  {expedientes.map((exp) => (
                    <option key={exp.id} value={exp.id}>{exp.numero}</option>
                  ))}
                </select>
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
              style={{ background: "white", borderRadius: "20px", padding: "28px", width: "400px", maxHeight: "85vh", overflowY: "auto" }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                <h2 style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <Receipt size={20} />
                  Factura {detalle.numero}
                </h2>
                <span onClick={() => setDetalle(null)} style={{ cursor: "pointer", fontSize: "22px" }}>&times;</span>
              </div>

              <p>
                <span style={{
                  background: (estadoColors[detalle.estado] || estadoColors.pendiente).bg,
                  color: (estadoColors[detalle.estado] || estadoColors.pendiente).color,
                  padding: "4px 12px", borderRadius: "30px", fontSize: "12px", fontWeight: 600,
                }}>
                  {(estadoColors[detalle.estado] || estadoColors.pendiente).label}
                </span>
              </p>

              <div style={{ display: "grid", gap: "14px", marginTop: "16px" }}>
                <DetalleItem label="Cliente" value={detalle.cliente_nombre || "Sin cliente asignado"} />
                <DetalleItem label="Concepto" value={detalle.concepto} />
                <DetalleItem label="Monto" value={formatMonto(detalle.monto)} />
                <DetalleItem label="Expediente" value={detalle.expediente_numero || "Sin expediente asociado"} />
                <DetalleItem label="Fecha de emisión" value={detalle.fecha_emision} />
                <DetalleItem label="Fecha de vencimiento" value={detalle.fecha_vencimiento || "No definida"} />
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}

function TarjetaResumen({ label, valor, color }) {
  return (
    <div style={{ background: "white", borderRadius: "16px", padding: "20px 24px", border: "1px solid #eef2f6", boxShadow: "0 2px 8px rgba(0,0,0,0.04)" }}>
      <div style={{ fontSize: "14px", color: "#6b7f96", marginBottom: "8px" }}>{label}</div>
      <div style={{ fontSize: "24px", fontWeight: "bold", color }}>{valor}</div>
    </div>
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