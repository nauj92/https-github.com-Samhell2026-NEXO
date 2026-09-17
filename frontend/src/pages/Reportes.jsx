import { useEffect, useState } from "react";
import { Flag, TrendingUp, Award, Users2, Search } from "lucide-react";
import api from "../api";
import Layout from "../components/Layout";

export default function Reportes() {
  const [expedientes, setExpedientes] = useState([]);
  const [facturas, setFacturas] = useState([]);
  const [clientes, setClientes] = useState([]);
  const [error, setError] = useState("");
  const [busqueda, setBusqueda] = useState("");
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get("/expedientes/"),
      api.get("/facturas/"),
      api.get("/clientes/"),
    ])
      .then(([expRes, facRes, cliRes]) => {
        setExpedientes(expRes.data);
        setFacturas(facRes.data);
        setClientes(cliRes.data);
      })
      .catch(() => setError("No se pudieron cargar los reportes."))
      .finally(() => setCargando(false));
  }, []);

  const formatMonto = (monto) =>
    new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(monto);

  // Rendimiento por abogado: cuántos casos tiene, cuántos activos, cuántos cerrados
  const rendimientoAbogados = () => {
    const mapa = {};
    expedientes.forEach((exp) => {
      const nombre = exp.abogado_asignado_nombre || "Sin asignar";
      if (!mapa[nombre]) mapa[nombre] = { nombre, total: 0, activos: 0, cerrados: 0 };
      mapa[nombre].total += 1;
      if (exp.estado === "activo") mapa[nombre].activos += 1;
      if (exp.estado === "cerrado") mapa[nombre].cerrados += 1;
    });
    return Object.values(mapa).sort((a, b) => b.total - a.total);
  };

  // Ranking de clientes por monto facturado
  const rankingClientes = () => {
    const mapa = {};
    facturas.forEach((fac) => {
      const nombre = fac.cliente_nombre || "Sin cliente";
      if (!mapa[nombre]) mapa[nombre] = { nombre, total: 0, cantidad: 0 };
      mapa[nombre].total += Number(fac.monto);
      mapa[nombre].cantidad += 1;
    });
    return Object.values(mapa).sort((a, b) => b.total - a.total).slice(0, 5);
  };

  // Distribución por materia como tabla (no gráfico, para diferenciarse del Dashboard)
  const materiasResumen = () => {
    const mapa = {};
    expedientes.forEach((exp) => {
      const materia = exp.materia || "Sin materia";
      if (!mapa[materia]) mapa[materia] = { materia, total: 0, activos: 0 };
      mapa[materia].total += 1;
      if (exp.estado === "activo") mapa[materia].activos += 1;
    });
    return Object.values(mapa).filter((m) => m.materia.toLowerCase().includes(busqueda.toLowerCase()));
  };

  const abogados = rendimientoAbogados();
  const clientesTop = rankingClientes();
  const materias = materiasResumen();

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
            <Flag size={22} />
            Reportes
          </div>

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
              placeholder="Buscar materia..."
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              style={{ border: "none", background: "transparent", outline: "none", fontSize: "14px", width: "100%" }}
            />
          </div>
        </header>

        <main style={{ padding: "32px" }}>
          {error && <p style={{ color: "#c73a3a" }}>{error}</p>}
          {cargando && <p>Cargando reportes...</p>}

          {!cargando && !error && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
              {/* Rendimiento por abogado */}
              <div style={{ background: "white", borderRadius: "16px", padding: "20px 24px", border: "1px solid #eef2f6" }}>
                <h3 style={{ marginBottom: "16px", color: "#1a2c3e", display: "flex", alignItems: "center", gap: "8px" }}>
                  <Users2 size={18} />
                  Rendimiento por Abogado
                </h3>
                {abogados.length === 0 && <p style={{ color: "#6b7f96" }}>Sin datos aún.</p>}
                {abogados.map((ab) => (
                  <div key={ab.nombre} style={{ padding: "12px 0", borderBottom: "1px solid #f0f3f8" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                      <strong style={{ fontSize: "14px" }}>{ab.nombre}</strong>
                      <span style={{ fontSize: "13px", color: "#6b7f96" }}>{ab.total} caso{ab.total !== 1 ? "s" : ""}</span>
                    </div>
                    <div style={{ display: "flex", gap: "12px", fontSize: "12px" }}>
                      <span style={{ color: "#1b8b5e" }}>● {ab.activos} activos</span>
                      <span style={{ color: "#5b6f84" }}>● {ab.cerrados} cerrados</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Ranking de clientes por facturación */}
              <div style={{ background: "white", borderRadius: "16px", padding: "20px 24px", border: "1px solid #eef2f6" }}>
                <h3 style={{ marginBottom: "16px", color: "#1a2c3e", display: "flex", alignItems: "center", gap: "8px" }}>
                  <Award size={18} />
                  Top Clientes por Facturación
                </h3>
                {clientesTop.length === 0 && <p style={{ color: "#6b7f96" }}>Sin datos aún.</p>}
                {clientesTop.map((cli, index) => (
                  <div key={cli.nombre} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 0", borderBottom: "1px solid #f0f3f8" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <span
                        style={{
                          width: "24px", height: "24px", borderRadius: "50%",
                          background: index === 0 ? "#d4a743" : "#eef2f6",
                          color: index === 0 ? "white" : "#6b7f96",
                          display: "flex", alignItems: "center", justifyContent: "center",
                          fontSize: "12px", fontWeight: 700, flexShrink: 0,
                        }}
                      >
                        {index + 1}
                      </span>
                      <span style={{ fontSize: "14px" }}>{cli.nombre}</span>
                    </div>
                    <div style={{ textAlign: "right" }}>
                      <div style={{ fontWeight: 600, fontSize: "14px" }}>{formatMonto(cli.total)}</div>
                      <div style={{ fontSize: "11px", color: "#6b7f96" }}>{cli.cantidad} factura{cli.cantidad !== 1 ? "s" : ""}</div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Distribución por materia — tabla, no gráfico */}
              <div style={{ background: "white", borderRadius: "16px", padding: "20px 24px", border: "1px solid #eef2f6", gridColumn: "1 / -1" }}>
                <h3 style={{ marginBottom: "16px", color: "#1a2c3e", display: "flex", alignItems: "center", gap: "8px" }}>
                  <TrendingUp size={18} />
                  Casos por Materia
                </h3>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
                  <thead>
                    <tr style={{ background: "#f8fafc" }}>
                      <th style={thStyle}>Materia</th>
                      <th style={thStyle}>Total de Casos</th>
                      <th style={thStyle}>Activos</th>
                    </tr>
                  </thead>
                  <tbody>
                    {materias.map((m) => (
                      <tr key={m.materia} style={{ borderTop: "1px solid #f0f3f8" }}>
                        <td style={tdStyle}><strong>{m.materia}</strong></td>
                        <td style={tdStyle}>{m.total}</td>
                        <td style={tdStyle}>{m.activos}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {materias.length === 0 && (
                  <p style={{ padding: "16px 0", color: "#6b7f96" }}>No hay materias que coincidan.</p>
                )}
              </div>
            </div>
          )}
        </main>
      </div>
    </Layout>
  );
}

const thStyle = { textAlign: "left", padding: "12px 16px", color: "#6b7f96", fontWeight: 600, borderBottom: "1px solid #e9edf2" };
const tdStyle = { padding: "12px 16px" };