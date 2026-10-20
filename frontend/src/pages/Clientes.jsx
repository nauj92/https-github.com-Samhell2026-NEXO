import { useEffect, useState } from "react";
import { Users, User, Search } from "lucide-react";
import api from "../api";
import { mensajeError } from "../utils/errores";
import Layout from "../components/Layout";

export default function Clientes() {
  const [clientes, setClientes] = useState([]);
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
    nombre: "",
    tipo_documento: "CC",
    numero_documento: "",
    telefono: "",
    email: "",
    direccion: "",
  });

  const cargarClientes = () => {
    setCargando(true);
    api
      .get("/clientes/")
      .then((response) => setClientes(response.data))
      .catch(() => setError("No se pudieron cargar los clientes."))
      .finally(() => setCargando(false));
  };

  useEffect(() => {
    cargarClientes();
    api.get("/expedientes/").then((response) => setExpedientes(response.data)).catch(() => {});
  }, []);

  const resumenCasos = (clienteId) => {
    const coincidencias = expedientes.filter((exp) => exp.cliente === clienteId);
    if (coincidencias.length === 0) return "Sin casos asignados";

    const activos = coincidencias.filter((e) => e.estado === "activo").length;
    const tramite = coincidencias.filter((e) => e.estado === "tramite").length;
    const cerrados = coincidencias.filter((e) => e.estado === "cerrado").length;

    const partes = [];
    if (activos > 0) partes.push(`${activos} caso${activos > 1 ? "s" : ""} activo${activos > 1 ? "s" : ""}`);
    if (tramite > 0) partes.push(`${tramite} en trámite`);
    if (cerrados > 0) partes.push(`${cerrados} cerrado${cerrados > 1 ? "s" : ""}`);

    return partes.join(", ");
  };

  const clientesFiltrados = clientes.filter(
  (cli) =>
    cli.nombre.toLowerCase().includes(busqueda.toLowerCase()) ||
    cli.numero_documento.toLowerCase().includes(busqueda.toLowerCase())
  );

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleNuevoClick = () => {
    setForm({ nombre: "", tipo_documento: "CC", numero_documento: "", telefono: "", email: "", direccion: "" });
    setEditandoId(null);
    setFormError("");
    setMostrarForm(true);
  };

  const handleEditar = (cli) => {
    setForm({
      nombre: cli.nombre,
      tipo_documento: cli.tipo_documento,
      numero_documento: cli.numero_documento,
      telefono: cli.telefono || "",
      email: cli.email || "",
      direccion: cli.direccion || "",
    });
    setEditandoId(cli.id);
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
        await api.patch(`/clientes/${editandoId}/`, form);
      } else {
        await api.post("/clientes/", form);
      }
      setMostrarForm(false);
      setEditandoId(null);
      setForm({ nombre: "", tipo_documento: "CC", numero_documento: "", telefono: "", email: "", direccion: "" });
      cargarClientes();
    } catch (err) {
      setFormError(mensajeError(err, "No se pudo guardar el cliente."));
    } finally {
      setGuardando(false);
    }
  };

  const handleEliminar = async (id) => {
    if (!window.confirm("¿Seguro que quieres eliminar este cliente?")) return;
    try {
      await api.delete(`/clientes/${id}/`);
      cargarClientes();
    } catch (err) {
      alert(mensajeError(err, "No se pudo eliminar el cliente."));
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
            <Users size={22} color="#0a1a2b" />
            Clientes
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
                placeholder="Buscar cliente..."
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
              + Nuevo Cliente
            </button>
          </div>
        </header>

        <main style={{ padding: "32px" }}>
          {error && <p style={{ color: "#c73a3a" }}>{error}</p>}
          {cargando && <p>Cargando clientes...</p>}

          {!cargando && !error && (
            <div
              style={{
                background: "white",
                borderRadius: "16px",
                border: "1px solid #eef2f6",
                padding: "20px 24px",
              }}
            >
              <h3 style={{ marginBottom: "16px", color: "#1a2c3e", display: "flex", alignItems: "center", gap: "8px" }}>
                <Users size={18} />
                Clientes Destacados
              </h3>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(220px,1fr))",
                  gap: "16px",
                }}
              >
                {clientesFiltrados.length === 0 && (
                  <p style={{ color: "#6b7f96" }}>No hay clientes que coincidan.</p>
                )}
                {clientesFiltrados.map((cli) => (
                  <div key={cli.id} style={{ background: "#f8fafc", padding: "16px", borderRadius: "12px" }}>
                    <strong>{cli.nombre}</strong>
                    <br />
                    <span style={{ fontSize: "13px", color: "#6b7f96" }}>
                      {resumenCasos(cli.id)}
                    </span>
                    <div style={{ marginTop: "10px" }}>
                      <span onClick={() => setDetalle(cli)} style={{ color: "#1f3b57", fontWeight: 600, cursor: "pointer", textDecoration: "underline", marginRight: "12px", fontSize: "13px" }}>Ver</span>
                      <span onClick={() => handleEditar(cli)} style={{ color: "#a8681a", fontWeight: 600, cursor: "pointer", textDecoration: "underline", marginRight: "12px", fontSize: "13px" }}>Editar</span>
                      <span onClick={() => handleEliminar(cli.id)} style={{ color: "#c73a3a", fontWeight: 600, cursor: "pointer", textDecoration: "underline", fontSize: "13px" }}>Eliminar</span>
                    </div>
                  </div>
                ))}
              </div>
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
              <h2 style={{ marginBottom: "16px" }}>{editandoId ? "✏️ Editar Cliente" : "+ Nuevo Cliente"}</h2>
              {formError && <p style={{ color: "#c73a3a", fontSize: "13px", whiteSpace: "pre-line" }}>{formError}</p>}

              <Campo label="Nombre completo">
                <input name="nombre" value={form.nombre} onChange={handleChange} required style={inputStyle} />
              </Campo>

              <Campo label="Tipo de documento">
                <select name="tipo_documento" value={form.tipo_documento} onChange={handleChange} style={inputStyle}>
                  <option value="CC">Cédula de Ciudadanía</option>
                  <option value="CE">Cédula de Extranjería</option>
                  <option value="NIT">NIT</option>
                  <option value="PA">Pasaporte</option>
                </select>
              </Campo>

              <Campo label="Número de documento">
                <input name="numero_documento" value={form.numero_documento} onChange={handleChange} required style={inputStyle} />
              </Campo>

              <Campo label="Teléfono">
                <input name="telefono" value={form.telefono} onChange={handleChange} style={inputStyle} />
              </Campo>

              <Campo label="Email">
                <input type="email" name="email" value={form.email} onChange={handleChange} style={inputStyle} />
              </Campo>

              <Campo label="Dirección">
                <input name="direccion" value={form.direccion} onChange={handleChange} style={inputStyle} />
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
              style={{ background: "white", borderRadius: "20px", padding: "28px", width: "380px", maxHeight: "85vh", overflowY: "auto" }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                <h2 style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <User size={20} />
                  {detalle.nombre}
                </h2>
                <span onClick={() => setDetalle(null)} style={{ cursor: "pointer", fontSize: "22px" }}>&times;</span>
              </div>

              <div style={{ display: "grid", gap: "14px" }}>
                <DetalleItem label="Tipo de documento" value={detalle.tipo_documento} />
                <DetalleItem label="Número de documento" value={detalle.numero_documento} />
                <DetalleItem label="Teléfono" value={detalle.telefono || "No registrado"} />
                <DetalleItem label="Email" value={detalle.email || "No registrado"} />
                <DetalleItem label="Dirección" value={detalle.direccion || "No registrada"} />
                <DetalleItem label="Casos" value={resumenCasos(detalle.id)} />
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