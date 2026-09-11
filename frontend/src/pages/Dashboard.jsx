import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { useNavigate } from "react-router-dom";
import api from "../api";
import Layout from "../components/Layout";
import { FolderOpen, CalendarCheck, Clock, Coins, Search, Bell, Settings, LayoutDashboard, TrendingUp, History, Gavel } from "lucide-react";

const coloresMateria = ["#1f3b57", "#3a5f7a", "#d4a743", "#6b8fa0", "#a67c52", "#c73a3a"];

const iconosPorTipo = {
  audiencia: Gavel,
  plazo: Clock,
  factura: Coins,
  general: Bell,
};

function tiempoRelativo(fechaISO) {
  const ahora = new Date();
  const fecha = new Date(fechaISO);
  const diffMs = ahora - fecha;
  const diffHoras = Math.floor(diffMs / (1000 * 60 * 60));
  if (diffHoras < 1) return "hace unos minutos";
  if (diffHoras < 24) return `hace ${diffHoras}h`;
  const diffDias = Math.floor(diffHoras / 24);
  if (diffDias === 1) return "ayer";
  return `hace ${diffDias} días`;
}

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [expedientes, setExpedientes] = useState([]);
  const [notificaciones, setNotificaciones] = useState([]);
  const [busqueda, setBusqueda] = useState("");
  const [error, setError] = useState("");
  const [mostrarNotifs, setMostrarNotifs] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    api
      .get("/dashboard/stats/")
      .then((response) => setStats(response.data))
      .catch(() => setError("No se pudieron cargar las estadísticas."));

    api
      .get("/expedientes/")
      .then((response) => setExpedientes(response.data))
      .catch(() => {});

    api
      .get("/notificaciones/")
      .then((response) => setNotificaciones(response.data))
      .catch(() => {});
  }, []);

  const marcarComoLeida = (id) => {
    api
      .patch(`/notificaciones/${id}/`, { leida: true })
      .then(() => {
        setNotificaciones((prev) =>
          prev.map((n) => (n.id === id ? { ...n, leida: true } : n))
        );
      })
      .catch(() => {});
  };

  const formatMonto = (monto) =>
    new Intl.NumberFormat("es-CO", {
      style: "currency",
      currency: "COP",
      maximumFractionDigits: 0,
    }).format(monto);

    const cards = stats
    ?[
       { label: "Casos Activos", value: stats.casos_activos, Icon: FolderOpen, tendencia: null },
       { label: "Audiencias Pendientes", value: stats.audiencias_pendientes, Icon: CalendarCheck, tendencia: stats.audiencias_hoy > 0 ? `⚠ ${stats.audiencias_hoy} para hoy` : null },
       { label: "Plazos Procesales", value: stats.plazos_procesales, Icon: Clock, tendencia: stats.plazos_procesales > 0 ? "⚠ Requieren atención" : null },
       { label: "Ingresos (Mes)", value: formatMonto(stats.ingresos_mes), Icon: Coins, tendencia: null },
     ]
    :[];

   const notificacionesNoLeidas = notificaciones.filter((n) => !n.leida).length;

   const expedientesFiltrados = expedientes.filter(
    (exp) =>
      exp.numero.toLowerCase().includes(busqueda.toLowerCase()) ||
      exp.demandante.toLowerCase().includes(busqueda.toLowerCase()) ||
      exp.demandado.toLowerCase().includes(busqueda.toLowerCase())
  );

  const datosGrafico = (stats?.casos_por_materia || []).map((item) => ({
    materia: item.materia || "Sin materia",
    total: item.total,
  }));

  return (
    <Layout>
      <div style={{ minHeight: "100vh", background: "#f4f7fb", fontFamily: "sans-serif" }}>
        {/* Barra superior */}
        <header
          style={{
            background: "white",
            padding: "16px 32px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            borderBottom: "1px solid #e9edf2",
          }}
        >
          <div style={{ fontSize: "20px", fontWeight: "bold", color: "#0a1a2b", display: "flex", alignItems: "center", gap: "10px" }}>
            <LayoutDashboard size={22} />
            Panel de Control
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "20px" }}>
            <div
              style={{
                background: "#f4f7fb",
                padding: "8px 16px",
                borderRadius: "30px",
                display: "flex",
                alignItems: "center",
                gap: "10px",
                border: "1px solid #e9edf2",
                width: "240px",
              }}
            >
              <Search size={16} color="#8899b4" />
              <input
                type="text"
                placeholder="Buscar expediente..."
                value={busqueda}
                onChange={(e) => setBusqueda(e.target.value)}
                style={{
                  border: "none",
                  background: "transparent",
                  outline: "none",
                  fontSize: "14px",
                  width: "100%",
                }}
              />
            </div>

            <div style={{ position: "relative" }}>
              <Bell size={20} color="#0a1a2b" style={{ cursor: "pointer" }} onClick={() => setMostrarNotifs(!mostrarNotifs)} />
              {notificacionesNoLeidas > 0 && (
                <span
                  style={{
                    position: "absolute",
                    top: "-4px",
                    right: "-6px",
                    background: "#c73a3a",
                    color: "white",
                    borderRadius: "50%",
                    fontSize: "10px",
                    width: "16px",
                    height: "16px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  {notificacionesNoLeidas}
                </span>
              )}

              {mostrarNotifs && (
                <div
                  style={{
                    position: "absolute",
                    top: "32px",
                    right: 0,
                    width: "280px",
                    background: "white",
                    borderRadius: "12px",
                    boxShadow: "0 8px 24px rgba(0,0,0,0.15)",
                    border: "1px solid #eef2f6",
                    zIndex: 10,
                    maxHeight: "300px",
                    overflowY: "auto",
                  }}
                >
                  {notificaciones.length === 0 && (
                    <p style={{ padding: "16px", color: "#6b7f96", fontSize: "13px" }}>
                      No hay notificaciones.
                    </p>
                  )}
                  {notificaciones.slice(0, 8).map((n) => (
                    <div
                      key={n.id}
                      onClick={() => marcarComoLeida(n.id)}
                      style={{
                        padding: "12px 16px",
                        borderBottom: "1px solid #f0f3f8",
                        fontSize: "13px",
                        background: n.leida ? "white" : "#fef8f8",
                        cursor: "pointer",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        gap: "8px",
                      }}
                    >
                      <span>{n.mensaje}</span>
                      {!n.leida && (
                        <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#c73a3a", flexShrink: 0 }} />
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <Settings size={20} color="#0a1a2b" style={{ cursor: "pointer" }} onClick={() => navigate("/configuracion")} />
          </div>
        </header>

        <main style={{ padding: "32px" }}>
          {error && <p style={{ color: "#c73a3a" }}>{error}</p>}
          {!stats && !error && <p>Cargando estadísticas...</p>}

          {/* Tarjetas de estadísticas */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(4, 1fr)",
              gap: "24px",
              marginBottom: "30px",
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
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                  <span style={{ fontSize: "14px", color: "#6b7f96" }}>{card.label}</span>
                  <card.Icon size={22} color="#d4a743" />
                </div>
                <div style={{ fontSize: "28px", fontWeight: "bold", color: "#0a1a2b" }}>
                  {card.value}
                </div>
                {card.tendencia && (
                  <div style={{ fontSize: "12px", color: "#c73a3a", marginTop: "6px", fontWeight: 500 }}>
                    {card.tendencia}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Gráfico + Actividad Reciente */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "2fr 1fr",
              gap: "24px",
              marginBottom: "30px",
            }}
          >
            <div
              style={{
                background: "white",
                borderRadius: "16px",
                padding: "20px 24px",
                border: "1px solid #eef2f6",
                boxShadow: "0 2px 8px rgba(0,0,0,0.04)",
              }}
            >
              <h3 style={{ marginBottom: "16px", color: "#1a2c3e", display: "flex", alignItems: "center", gap: "8px" }}>
                <TrendingUp size={18} />
                Casos por Área Judicial
              </h3>
              {datosGrafico.length === 0 ? (
                <p style={{ color: "#6b7f96" }}>Aún no hay datos suficientes.</p>
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={datosGrafico}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f3f8" />
                    <XAxis dataKey="materia" tick={{ fontSize: 12 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="total" radius={[6, 6, 0, 0]}>
                      {datosGrafico.map((_, index) => (
                        <Cell key={index} fill={coloresMateria[index % coloresMateria.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            <div
              style={{
                background: "white",
                borderRadius: "16px",
                padding: "20px 24px",
                border: "1px solid #eef2f6",
                boxShadow: "0 2px 8px rgba(0,0,0,0.04)",
              }}
            >
              <h3 style={{ marginBottom: "16px", color: "#1a2c3e", display: "flex", alignItems: "center", gap: "8px" }}>
                <History size={18} />
                Actividad Reciente
              </h3>

              {notificaciones.length === 0 && (
                <p style={{ color: "#6b7f96", fontSize: "14px" }}>
                  No hay actividad reciente registrada.
                </p>
              )}

              {notificaciones.slice(0, 6).map((notif) => {
                const partes = notif.mensaje.split(" ");
                const primeraParte = partes.slice(0, 2).join(" ");
                const resto = partes.slice(2).join(" ");
                const esUrgente = notif.tipo === "plazo" && !notif.leida;

                return (
                  <div
                    key={notif.id}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "14px",
                      padding: "12px 0",
                      borderBottom: "1px solid #f0f3f8",
                    }}
                  >
                    <div
                      style={{
                        width: "36px",
                        height: "36px",
                        borderRadius: "10px",
                        background: notif.leida ? "#eef3fa" : "#fde8e8",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        flexShrink: 0,
                      }}
                    >
                      {(() => {
                        const IconoNotif = iconosPorTipo[notif.tipo] || Bell;
                        return <IconoNotif size={16} color="#1f3b57" />;
                      })()}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: "14px" }}>
                        <strong>{primeraParte}</strong> {resto}
                      </div>
                      {esUrgente && (
                        <span
                          style={{
                            display: "inline-block",
                            marginTop: "4px",
                            background: "#fde8e8",
                            color: "#c73a3a",
                            padding: "2px 10px",
                            borderRadius: "30px",
                            fontSize: "10px",
                            fontWeight: 700,
                          }}
                        >
                          URGENTE
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: "12px", color: "#8899b4", whiteSpace: "nowrap" }}>
                      {tiempoRelativo(notif.creada_en)}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Resultados de búsqueda */}
          {busqueda && (
            <div
              style={{
                background: "white",
                borderRadius: "16px",
                padding: "20px 24px",
                border: "1px solid #eef2f6",
                boxShadow: "0 2px 8px rgba(0,0,0,0.04)",
              }}
            >
              <h3 style={{ marginBottom: "16px", color: "#1a2c3e" }}>
                🔍 Resultados para "{busqueda}" ({expedientesFiltrados.length})
              </h3>
              {expedientesFiltrados.length === 0 && (
                <p style={{ color: "#6b7f96" }}>No se encontraron expedientes.</p>
              )}
              {expedientesFiltrados.map((exp) => (
                <div
                  key={exp.id}
                  style={{
                    padding: "10px 0",
                    borderBottom: "1px solid #f0f3f8",
                    display: "flex",
                    justifyContent: "space-between",
                  }}
                >
                  <span>
                    <strong>{exp.numero}</strong> — {exp.demandante} vs. {exp.demandado}
                  </span>
                </div>
              ))}
            </div>
          )}
        </main>
      </div>
    </Layout>
  );
}