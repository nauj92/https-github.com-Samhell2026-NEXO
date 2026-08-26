import { useEffect, useState } from "react";
import api from "../api";
import Layout from "../components/Layout";

export default function Reportes() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    api.get("/dashboard/stats/").then((response) => setStats(response.data));
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
          🚩 Reportes
        </header>
        <main style={{ padding: "32px" }}>
          {!stats && <p>Cargando...</p>}
          {stats && (
            <div
              style={{
                background: "white",
                borderRadius: "16px",
                padding: "24px",
                border: "1px solid #eef2f6",
              }}
            >
              <p>Casos activos: <strong>{stats.casos_activos}</strong></p>
              <p>Casos en trámite: <strong>{stats.casos_tramite}</strong></p>
              <p>Casos cerrados: <strong>{stats.casos_cerrados}</strong></p>
              <p>Distribución por materia:</p>
              <ul>
                {stats.casos_por_materia.map((m) => (
                  <li key={m.materia}>{m.materia}: {m.total}</li>
                ))}
              </ul>
            </div>
          )}
        </main>
      </div>
    </Layout>
  );
}