import Layout from "../components/Layout";
import { useEffect, useState } from "react";
import api from "../api";

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/dashboard/stats/")
      .then((response) => setStats(response.data))
      .catch(() => setError("No se pudieron cargar las estadísticas."));
  }, []);

  const cards = stats
    ? [
        { label: "Casos Activos", value: stats.casos_activos, icon: "📁", color: "#1f3b57" },
        { label: "Casos En Trámite", value: stats.casos_tramite, icon: "⏳", color: "#a8681a" },
        { label: "Casos Cerrados", value: stats.casos_cerrados, icon: "✅", color: "#5b6f84" },
        { label: "Audiencias (7 días)", value: stats.audiencias_pendientes, icon: "📅", color: "#c73a3a" },
      ]
    : [];

  return (
    <Layout>
    <div style={{ minHeight: "100vh", background: "#f4f7fb", fontFamily: "sans-serif" }}>
      <header
        style={{
          background: "#0a1a2b",
          color: "white",
          padding: "16px 32px",
          fontSize: "20px",
          fontWeight: "bold",
        }}
      >
        ⚖️ ERP — Panel de Control.
      </header>

      <main style={{ padding: "32px" }}>
        {error && <p style={{ color: "#c73a3a" }}>{error}</p>}

        {!stats && !error && <p>Cargando estadísticas...</p>}

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(4, 1fr)",
            gap: "24px",
          }}
        >
          {cards.map((card) => (
            <div
              key={card.label}
              style={{
                background: "white",
                borderRadius: "16px",
                padding: "20px 24px",
                boxShadow: "0 2px 8px rgba(0,0,0,0.04)",
                border: "1px solid #eef2f6",
              }}
            >
              <div style={{ fontSize: "28px", marginBottom: "8px" }}>{card.icon}</div>
              <div style={{ fontSize: "14px", color: "#6b7f96", marginBottom: "8px" }}>
                {card.label}
              </div>
              <div style={{ fontSize: "32px", fontWeight: "bold", color: card.color }}>
                {card.value}
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
    </Layout>
  );
}