import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { LayoutDashboard, ChevronDown, ChevronRight, FileText, FileSignature, CalendarDays, Briefcase, Users, Contact, Gavel } from "lucide-react";
import api from "../api";
import Layout from "../components/Layout";
import { mensajeError } from "../utils/errores";
import { Encabezado } from "../components/ui";

const CLAVE = "dashboard_paneles";
const ESTADOS_DEMANDA = {
  elaboracion: "En elaboración", radicada: "Radicada", inadmitida: "Inadmitida (subsanar)",
  admitida: "Admitida", rechazada: "Rechazada", retirada: "Retirada",
};

function leer() {
  try {
    return JSON.parse(localStorage.getItem(CLAVE)) || {};
  } catch {
    return {};
  }
}

const COLOR_RAMA = { Civil: "#2f5d8a", Familia: "#b05a9a", Laboral: "#2e8b6e", Penal: "#c0504d", Administrativo: "#d9822b", Constitucional: "#2a8fa6", Otras: "#8a97a8" };

const fechaCorta = (iso) => {
  const [a, m, d] = String(iso).slice(0, 10).split("-");
  return `${d}/${m}/${a}`;
};
const fechaHora = (iso) => new Date(iso).toLocaleString("es-CO", { dateStyle: "short", timeStyle: "short" });

function Tarjeta({ titulo, valor, Icono, color = "#2f5d8a", alerta }) {
  return (
    <div style={{ background: `linear-gradient(135deg, ${color}18 0%, #ffffff 70%)`, border: `1px solid ${alerta ? "#f0b8b8" : color + "33"}`, borderLeft: `5px solid ${color}`, borderRadius: "14px", padding: "16px 18px", display: "flex", alignItems: "center", gap: "14px", boxShadow: "0 1px 3px rgba(20,48,79,0.06)" }}>
      <div style={{ background: color, borderRadius: "12px", padding: "10px", display: "flex" }}>
        <Icono size={22} color="white" />
      </div>
      <div>
        <div style={{ fontSize: "28px", fontWeight: 700, color: alerta ? "#c73a3a" : "#14304f", lineHeight: 1.1 }}>{valor}</div>
        <div style={{ fontSize: "13px", color: "#51667d" }}>{titulo}</div>
      </div>
    </div>
  );
}

// Panel que se despliega y se pliega; recuerda su estado en el navegador.
function Panel({ id, titulo, resumen, abierto, alternar, children, color = "#2f5d8a" }) {
  return (
    <section style={{ background: "white", border: `1px solid ${color}33`, borderRadius: "14px", marginBottom: "14px", overflow: "hidden", boxShadow: "0 1px 3px rgba(20,48,79,0.06)" }}>
      <button
        type="button"
        onClick={() => alternar(id)}
        aria-expanded={abierto}
        style={{ width: "100%", display: "flex", alignItems: "center", gap: "10px", padding: "14px 18px", background: `${color}14`, border: "none", borderLeft: `5px solid ${color}`, cursor: "pointer", textAlign: "left", fontSize: "15px", fontWeight: 700, color: "#14304f" }}
      >
        {abierto ? <ChevronDown size={18} color={color} /> : <ChevronRight size={18} color={color} />}
        <span style={{ flex: 1 }}>{titulo}</span>
        {resumen !== undefined && <span style={{ fontSize: "12px", fontWeight: 700, color, background: "white", border: `1px solid ${color}55`, borderRadius: "20px", padding: "3px 10px" }}>{resumen}</span>}
      </button>
      {abierto && <div style={{ padding: "6px 18px 16px" }}>{children}</div>}
    </section>
  );
}

function Lista({ items, vacio, render }) {
  if (!items.length) return <div style={{ color: "#8899b4", fontSize: "14px", padding: "6px 0" }}>{vacio}</div>;
  return (
    <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
      {items.map((it, i) => (
        <li key={it.id ?? i} style={{ display: "flex", justifyContent: "space-between", gap: "12px", padding: "10px 0", borderTop: i ? "1px solid #f0f3f7" : "none", fontSize: "14px" }}>
          {render(it)}
        </li>
      ))}
    </ul>
  );
}

const Vence = ({ dias }) => (
  <span style={{ fontWeight: 700, color: dias < 0 ? "#c73a3a" : dias <= 3 ? "#a8681a" : "#1f3b57", whiteSpace: "nowrap" }}>
    {dias < 0 ? `Vencido hace ${-dias} d` : dias === 0 ? "Vence hoy" : `En ${dias} d`}
  </span>
);

export default function Dashboard() {
  const [datos, setDatos] = useState(null);
  const [error, setError] = useState("");
  const [cerrados, setCerrados] = useState(leer); // id -> true si está plegado

  useEffect(() => {
    api.get("/dashboard/resumen/").then((r) => setDatos(r.data)).catch((e) => setError(mensajeError(e, "No se pudo cargar el dashboard.")));
  }, []);

  const alternar = (id) =>
    setCerrados((prev) => {
      const nuevo = { ...prev, [id]: !prev[id] };
      try {
        localStorage.setItem(CLAVE, JSON.stringify(nuevo));
      } catch {
        /* sin almacenamiento: funciona igual */
      }
      return nuevo;
    });
  const abierto = (id) => !cerrados[id];

  const d = datos;
  return (
    <Layout>
      <Encabezado Icono={LayoutDashboard} titulo="Dashboard" />
      <div style={{ padding: "24px 32px", background: "linear-gradient(180deg, #e8f0f9 0%, #f3f6fa 320px)", minHeight: "calc(100vh - 64px)" }}>
        <div style={{ maxWidth: "1100px" }}>
        <div style={{ background: "linear-gradient(120deg, #1d3f66 0%, #3b6ea5 100%)", color: "white", borderRadius: "16px", padding: "20px 24px", marginBottom: "20px", display: "flex", justifyContent: "space-between", gap: "12px", flexWrap: "wrap", alignItems: "center", borderBottom: "4px solid #d4a743" }}>
          <div>
            <div style={{ fontSize: "20px", fontWeight: 700 }}>Resumen del despacho</div>
            <div style={{ fontSize: "13px", opacity: 0.85 }}>Lo que necesita su atención, según su rol</div>
          </div>
          <div style={{ fontSize: "14px", fontWeight: 600, textTransform: "capitalize" }}>{new Date().toLocaleDateString("es-CO", { weekday: "long", day: "numeric", month: "long", year: "numeric" })}</div>
        </div>
        {error && <div style={{ color: "#c73a3a", marginBottom: "12px" }}>{error}</div>}
        {!d && !error && <div style={{ color: "#6b7f96" }}>Cargando…</div>}
        {d && (
          <>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "14px", marginBottom: "20px" }}>
              <Tarjeta titulo="Demandas" valor={d.totales.demandas} Icono={FileText} color="#2f5d8a" />
              <Tarjeta titulo="Contestaciones" valor={d.totales.contestaciones} Icono={FileSignature} alerta={d.contestaciones_vencidas > 0} color="#6b5ca5" />
              <Tarjeta titulo="Clientes" valor={d.totales.clientes} Icono={Contact} color="#2a8fa6" />
              {d.es_directivo && <Tarjeta titulo="Abogados" valor={d.totales.abogados} Icono={Users} color="#d4a743" />}
              <Tarjeta titulo="Audiencias" valor={d.totales.audiencias} Icono={CalendarDays} color="#2e8b6e" />
              <Tarjeta titulo="Diligencias judiciales" valor={d.totales.diligencias} Icono={Gavel} color="#d9822b" />
              <Tarjeta titulo="Expedientes (casos)" valor={d.totales.expedientes} Icono={Briefcase} color="#c0504d" />
            </div>

            <Panel color="#2f5d8a" id="ramas" titulo="Casos por rama del derecho" resumen={`${d.totales.expedientes} caso(s)`} abierto={abierto("ramas")} alternar={alternar}>
              {d.casos_por_rama.length === 0 && <div style={{ color: "#8899b4", fontSize: "14px" }}>Aún no hay casos registrados.</div>}
              {d.casos_por_rama.map((r) => (
                <div key={r.rama} style={{ marginBottom: "10px", fontSize: "14px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                    <span style={{ display: "flex", alignItems: "center", gap: "8px" }}><span style={{ width: "10px", height: "10px", borderRadius: "50%", background: COLOR_RAMA[r.rama] || "#2f5d8a" }} />{r.rama}</span>
                    <strong>{r.total}</strong>
                  </div>
                  <div style={{ background: "#eef2f6", borderRadius: "6px", height: "8px" }}>
                    <div style={{ width: `${Math.max(4, (r.total / d.totales.expedientes) * 100)}%`, background: COLOR_RAMA[r.rama] || "#2f5d8a", height: "8px", borderRadius: "6px" }} />
                  </div>
                </div>
              ))}
              <Link to="/expedientes" style={{ fontSize: "13px", fontWeight: 600 }}>Ir a expedientes</Link>
            </Panel>

            <Panel color="#6b5ca5" id="contestaciones" titulo="Contestaciones de demanda pendientes" resumen={`${d.contestaciones_pendientes_total} pendiente(s)${d.contestaciones_vencidas ? ` · ${d.contestaciones_vencidas} vencida(s)` : ""}`} abierto={abierto("contestaciones")} alternar={alternar}>
              <Lista
                items={d.contestaciones_pendientes}
                vacio="No hay contestaciones pendientes con fecha de notificación."
                render={(c) => (
                  <>
                    <span><strong>{c.titulo}</strong><br /><span style={{ color: "#6b7f96" }}>Demandante: {c.referencia} · vence {fechaCorta(c.fecha_limite)}</span></span>
                    <Vence dias={c.dias} />
                  </>
                )}
              />
              <Link to="/contestaciones" style={{ fontSize: "13px", fontWeight: 600 }}>Ir a contestaciones</Link>
            </Panel>

            <Panel color="#c0504d" id="plazos" titulo="Plazos procesales (vencidos y próximos 7 días)" resumen={`${d.plazos.length}`} abierto={abierto("plazos")} alternar={alternar}>
              <Lista
                items={d.plazos}
                vacio="No hay plazos por atender."
                render={(p) => (
                  <>
                    <span><strong>{p.titulo}</strong><br /><span style={{ color: "#6b7f96" }}>Expediente {p.referencia} · {fechaCorta(p.fecha_limite)}</span></span>
                    <Vence dias={p.dias} />
                  </>
                )}
              />
            </Panel>

            <Panel color="#2e8b6e" id="audiencias" titulo="Audiencias y diligencias (próximos 30 días)" resumen={`${d.audiencias_proximas.length}`} abierto={abierto("audiencias")} alternar={alternar}>
              <Lista
                items={d.audiencias_proximas}
                vacio="No hay audiencias programadas."
                render={(a) => (
                  <>
                    <span><strong>{a.tipo}{a.clase ? ` · ${a.clase}` : ""}</strong><br /><span style={{ color: "#6b7f96" }}>Expediente {a.expediente} · {a.lugar}</span></span>
                    <span style={{ fontWeight: 600, whiteSpace: "nowrap" }}>{fechaHora(a.fecha_hora)}</span>
                  </>
                )}
              />
              <Link to="/audiencias" style={{ fontSize: "13px", fontWeight: 600 }}>Ir a audiencias</Link>
            </Panel>

            <Panel color="#d4a743" id="demandas" titulo="Demandas por estado" resumen={`${d.demandas_total} en total`} abierto={abierto("demandas")} alternar={alternar}>
              <Lista
                items={Object.entries(d.demandas_por_estado).map(([k, v]) => ({ id: k, nombre: ESTADOS_DEMANDA[k] || k, total: v }))}
                vacio="Aún no hay demandas registradas."
                render={(e) => (
                  <>
                    <span>{e.nombre}</span>
                    <strong>{e.total}</strong>
                  </>
                )}
              />
              <Link to="/demandas" style={{ fontSize: "13px", fontWeight: 600 }}>Ir a elaboración de demanda</Link>
            </Panel>

            <Panel color="#2a8fa6" id="expedientes" titulo="Expedientes" resumen={`${d.expedientes.activos + d.expedientes.tramite + d.expedientes.cerrados} en total`} abierto={abierto("expedientes")} alternar={alternar}>
              <Lista
                items={[
                  { id: "a", nombre: "Activos", total: d.expedientes.activos },
                  { id: "t", nombre: "En trámite", total: d.expedientes.tramite },
                  { id: "c", nombre: "Cerrados", total: d.expedientes.cerrados },
                ]}
                vacio=""
                render={(e) => (
                  <>
                    <span>{e.nombre}</span>
                    <strong>{e.total}</strong>
                  </>
                )}
              />
            </Panel>
          </>
        )}
        </div>
      </div>
    </Layout>
  );
}
