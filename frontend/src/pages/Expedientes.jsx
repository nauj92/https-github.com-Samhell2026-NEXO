import { useEffect, useState } from "react";
import api from "../api";
import Layout from "../components/Layout";

const estadoColors = {
  activo: { bg: "#e2f3e8", color: "#1b8b5e", label: "Activo" },
  tramite: { bg: "#fff3d6", color: "#a8681a", label: "En trámite" },
  cerrado: { bg: "#e9ecf0", color: "#5b6f84", label: "Cerrado" },
};

export default function Expedientes() {
  const [expedientes, setExpedientes] = useState([]);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    api
      .get("/expedientes/")
      .then((response) => setExpedientes(response.data))
      .catch(() => setError("No se pudieron cargar los expedientes."))
      .finally(() => setCargando(false));
  }, []);

  return (
    <Layout>
      <div style={{ minHeight: "100vh", background: "#f4f7fb", fontFamily: "sans-serif" }}>
        <header
          style={{
            background: "white",
            padding: "16px 32px",
            fontSize: "20px",
            fontWeight: "bold",
            borderBottom: "1px solid #e9edf2",
          }}
        >
          📂 Expedientes Judiciales
        </header>

        <main style={{ padding: "32px" }}>
          {error && <p style={{ color: "#c73a3a" }}>{error}</p>}
          {cargando && <p>Cargando expedientes...</p>}

          {!cargando && !error && (
            <div
              style={{
                background: "white",
                borderRadius: "16px",
                border: "1px solid #eef2f6",
                overflow: "hidden",
              }}
            >
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
                <thead>
                  <tr style={{ background: "#f8fafc" }}>
                    <th style={thStyle}>N° Expediente</th>
                    <th style={thStyle}>Demandante</th>
                    <th style={thStyle}>Demandado</th>
                    <th style={thStyle}>Juzgado</th>
                    <th style={thStyle}>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {expedientes.map((exp) => {
                    const estado = estadoColors[exp.estado] || estadoColors.activo;
                    return (
                      <tr key={exp.id} style={{ borderTop: "1px solid #f0f3f8" }}>
                        <td style={tdStyle}>
                          <strong>{exp.numero}</strong>
                        </td>
                        <td style={tdStyle}>{exp.demandante}</td>
                        <td style={tdStyle}>{exp.demandado}</td>
                        <td style={tdStyle}>{exp.juzgado_nombre}</td>
                        <td style={tdStyle}>
                          <span
                            style={{
                              background: estado.bg,
                              color: estado.color,
                              padding: "4px 12px",
                              borderRadius: "30px",
                              fontSize: "12px",
                              fontWeight: 600,
                            }}
                          >
                            {estado.label}
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
      </div>
    </Layout>
  );
}

const thStyle = {
  textAlign: "left",
  padding: "14px 16px",
  color: "#6b7f96",
  fontWeight: 600,
  borderBottom: "1px solid #e9edf2",
};

const tdStyle = {
  padding: "14px 16px",
};