import { useEffect, useState } from "react";
import { Bell } from "lucide-react";
import api from "../api";
import Layout from "../components/Layout";
import { mensajeError } from "../utils/errores";
import { Encabezado, Chip, botonSecundario } from "../components/ui";

const TIPOS = { audiencia: "Audiencia", plazo: "Plazo", factura: "Factura", general: "General" };

const fechaHora = (iso) =>
  new Date(iso).toLocaleString("es-CO", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });

export default function Notificaciones() {
  const [lista, setLista] = useState([]);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(true);
  const [soloPendientes, setSoloPendientes] = useState(false);

  useEffect(() => {
    api
      .get("/notificaciones/")
      .then((r) => setLista(r.data))
      .catch((err) => setError(mensajeError(err, "No se pudieron cargar las notificaciones.")))
      .finally(() => setCargando(false));
  }, []);

  const marcar = async (n) => {
    if (n.leida) return;
    try {
      await api.patch(`/notificaciones/${n.id}/`, { leida: true });
      setLista((prev) => prev.map((x) => (x.id === n.id ? { ...x, leida: true } : x)));
    } catch (err) {
      setError(mensajeError(err));
    }
  };

  const marcarTodas = async () => {
    const pendientes = lista.filter((n) => !n.leida);
    try {
      await Promise.all(pendientes.map((n) => api.patch(`/notificaciones/${n.id}/`, { leida: true })));
      setLista((prev) => prev.map((x) => ({ ...x, leida: true })));
    } catch (err) {
      setError(mensajeError(err));
    }
  };

  const noLeidas = lista.filter((n) => !n.leida).length;
  const visibles = soloPendientes ? lista.filter((n) => !n.leida) : lista;

  return (
    <Layout>
      <div style={{ minHeight: "100vh", background: "#f4f7fb", fontFamily: "sans-serif" }}>
        <Encabezado Icono={Bell} titulo="Notificaciones" />
        <main style={{ padding: "32px", maxWidth: "820px" }}>
          <p style={{ color: "#6b7f96", fontSize: "13px", marginTop: 0 }}>
            Avisos automáticos de audiencias y diligencias, plazos de subsanación y contestación, citaciones, vigilancia sin movimiento y facturas.
          </p>
          {error && <p style={{ color: "#c73a3a" }}>{error}</p>}
          {cargando && <p>Cargando...</p>}
          {!cargando && (
            <>
              <div style={{ display: "flex", gap: "10px", marginBottom: "16px", alignItems: "center", flexWrap: "wrap" }}>
                <Chip label={`Todas (${lista.length})`} activo={!soloPendientes} onClick={() => setSoloPendientes(false)} />
                <Chip label={`Sin leer (${noLeidas})`} activo={soloPendientes} onClick={() => setSoloPendientes(true)} bg="#fde8e8" color="#c73a3a" />
                {noLeidas > 0 && <button type="button" onClick={marcarTodas} style={botonSecundario}>Marcar todas como leídas</button>}
              </div>
              <div style={{ background: "white", borderRadius: "16px", border: "1px solid #eef2f6", overflow: "hidden" }}>
                {visibles.length === 0 && <p style={{ padding: "24px", color: "#6b7f96", margin: 0 }}>No hay notificaciones.</p>}
                {visibles.map((n) => (
                  <div
                    key={n.id}
                    onClick={() => marcar(n)}
                    style={{ padding: "14px 20px", borderBottom: "1px solid #f0f3f8", background: n.leida ? "white" : "#fef8f8", cursor: n.leida ? "default" : "pointer", display: "flex", justifyContent: "space-between", gap: "12px", alignItems: "center" }}
                  >
                    <span>
                      <span style={{ fontSize: "11px", color: "#6b7f96", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                        {TIPOS[n.tipo] || n.tipo} · {fechaHora(n.creada_en)}
                      </span>
                      <div style={{ fontSize: "14px", marginTop: "2px", fontWeight: n.leida ? 400 : 600 }}>{n.mensaje}</div>
                    </span>
                    {!n.leida && <span title="Sin leer" style={{ width: "9px", height: "9px", borderRadius: "50%", background: "#c73a3a", flexShrink: 0 }} />}
                  </div>
                ))}
              </div>
            </>
          )}
        </main>
      </div>
    </Layout>
  );
}
