import { useEffect, useState } from "react";
import { ShieldCheck } from "lucide-react";
import api from "../api";
import Layout from "../components/Layout";
import { mensajeError } from "../utils/errores";
import { Encabezado, Chip, inputStyle, thStyle, tdStyle, botonPrimario } from "../components/ui";

const fechaHora = (iso) => (iso ? new Date(iso).toLocaleString("es-CO", { dateStyle: "short", timeStyle: "short" }) : "—");

export default function Auditoria() {
  const [datos, setDatos] = useState(null);
  const [usuarios, setUsuarios] = useState([]);
  const [filtro, setFiltro] = useState({ usuario: "", desde: "", hasta: "" });
  const [pestana, setPestana] = useState("actividad");
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(true);

  const cargar = (f = filtro) => {
    setCargando(true);
    setError("");
    const params = Object.fromEntries(Object.entries(f).filter(([, v]) => v));
    api
      .get("/auditoria/", { params })
      .then((r) => setDatos(r.data))
      .catch((err) => setError(mensajeError(err, "No se pudo cargar la auditoría.")))
      .finally(() => setCargando(false));
  };

  useEffect(() => {
    cargar();
    api.get("/gestion-usuarios/").then((r) => setUsuarios(r.data)).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const set = (k) => (e) => setFiltro({ ...filtro, [k]: e.target.value });
  const limpiar = () => {
    const vacio = { usuario: "", desde: "", hasta: "" };
    setFiltro(vacio);
    cargar(vacio);
  };

  return (
    <Layout>
      <div style={{ minHeight: "100vh", background: "#f4f7fb", fontFamily: "sans-serif" }}>
        <Encabezado Icono={ShieldCheck} titulo="Auditoría" />
        <main style={{ padding: "32px" }}>
          <p style={{ color: "#6b7f96", fontSize: "13px", marginTop: 0 }}>
            Registro de solo lectura: quién hizo qué y cuándo en los expedientes, y los inicios de sesión.
          </p>
          <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", alignItems: "end", marginBottom: "16px" }}>
            <label style={{ fontSize: "13px" }}>Usuario<br />
              <select value={filtro.usuario} onChange={set("usuario")} style={{ ...inputStyle, minWidth: "220px" }}>
                <option value="">Todos</option>
                {usuarios.map((u) => <option key={u.id} value={u.id}>{u.nombre_completo}</option>)}
              </select>
            </label>
            <label style={{ fontSize: "13px" }}>Desde<br /><input type="date" value={filtro.desde} onChange={set("desde")} style={inputStyle} /></label>
            <label style={{ fontSize: "13px" }}>Hasta<br /><input type="date" value={filtro.hasta} onChange={set("hasta")} style={inputStyle} /></label>
            <button style={botonPrimario} onClick={() => cargar()}>Filtrar</button>
            <button style={{ ...botonPrimario, background: "#6b7f96" }} onClick={limpiar}>Limpiar</button>
          </div>
          <div style={{ display: "flex", gap: "10px", marginBottom: "16px" }}>
            <Chip label="Actividad" activo={pestana === "actividad"} onClick={() => setPestana("actividad")} />
            <Chip label="Inicios de sesión" activo={pestana === "accesos"} onClick={() => setPestana("accesos")} />
          </div>
          {error && <p style={{ color: "#c73a3a" }}>{error}</p>}
          {cargando && <p>Cargando...</p>}
          {datos && !cargando && pestana === "actividad" && (
            <div style={{ background: "white", borderRadius: "16px", border: "1px solid #eef2f6", overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
                <thead><tr style={{ background: "#f8fafc" }}>{["Fecha", "Usuario", "Acción", "Expediente", "Detalle"].map((h) => <th key={h} style={thStyle}>{h}</th>)}</tr></thead>
                <tbody>
                  {datos.actividad.map((a, i) => (
                    <tr key={i} style={{ borderTop: "1px solid #f0f3f8" }}>
                      <td style={tdStyle}>{fechaHora(a.fecha)}</td>
                      <td style={tdStyle}>{a.usuario}</td>
                      <td style={tdStyle}><strong>{a.accion}</strong></td>
                      <td style={tdStyle}>{a.expediente}</td>
                      <td style={{ ...tdStyle, color: "#51667d", maxWidth: "380px" }}>{a.detalle || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {datos.actividad.length === 0 && <p style={{ padding: "24px", color: "#6b7f96" }}>No hay actividad con esos filtros.</p>}
            </div>
          )}
          {datos && !cargando && pestana === "accesos" && (
            <>
              <div style={{ background: "white", borderRadius: "16px", border: "1px solid #eef2f6", overflowX: "auto", marginBottom: "20px" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
                  <thead><tr style={{ background: "#f8fafc" }}>{["Fecha", "Usuario", "Dirección IP", "Cierre de sesión"].map((h) => <th key={h} style={thStyle}>{h}</th>)}</tr></thead>
                  <tbody>
                    {datos.accesos.inicios.map((a, i) => (
                      <tr key={i} style={{ borderTop: "1px solid #f0f3f8" }}>
                        <td style={tdStyle}>{fechaHora(a.fecha)}</td>
                        <td style={tdStyle}>{a.usuario}</td>
                        <td style={tdStyle}>{a.ip || "—"}</td>
                        <td style={tdStyle}>{fechaHora(a.cierre)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {datos.accesos.inicios.length === 0 && <p style={{ padding: "24px", color: "#6b7f96" }}>No hay inicios de sesión registrados.</p>}
              </div>
              {datos.accesos.fallidos.length > 0 && (
                <>
                  <h3>Intentos fallidos vigentes</h3>
                  {datos.accesos.fallidos.map((a, i) => (
                    <p key={i} style={{ fontSize: "14px", margin: "4px 0" }}>{fechaHora(a.fecha)} · <strong>{a.usuario}</strong> · {a.ip || "—"} · {a.intentos} intento(s)</p>
                  ))}
                </>
              )}
            </>
          )}
        </main>
      </div>
    </Layout>
  );
}
