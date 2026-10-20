import { useEffect, useState } from "react";
import { Send } from "lucide-react";
import api from "../api";
import Layout from "../components/Layout";
import { mensajeError } from "../utils/errores";
import { fecha } from "../utils/formato";
import { Encabezado, Modal, Campo, Dato, Chip, Etiqueta, inputStyle, thStyle, tdStyle, botonSecundario, enlace, mensajeErrorEstilo } from "../components/ui";

const ESTADOS = {
  pendiente: { label: "Pendiente de envío", bg: "#e9ecf0", color: "#5b6f84" },
  enviada: { label: "Enviada", bg: "#e3effa", color: "#2a6aa8" },
  entregada: { label: "Entregada", bg: "#fff3d6", color: "#a8681a" },
  devuelta: { label: "Devuelta", bg: "#fde8e8", color: "#c73a3a" },
  notificado: { label: "Notificado", bg: "#e2f3e8", color: "#1b8b5e" },
};
const TIPOS = { citacion: "Citación (art. 291 CGP)", aviso: "Aviso (art. 292 CGP)" };
const UBICACIONES = { mismo_municipio: "Mismo municipio del juzgado (5 días hábiles)", otro_municipio: "Otro municipio (10 días hábiles)", exterior: "Exterior (30 días hábiles)" };

const VACIO = {
  destinatario: "", direccion: "", tipo: "citacion", ubicacion: "mismo_municipio", estado: "pendiente", demanda: "", expediente: "",
  fecha_envio: "", empresa_mensajeria: "", guia: "", fecha_entrega: "", fecha_notificacion: "", abogado_responsable: "", observaciones: "",
};
const NULABLES = ["demanda", "expediente", "fecha_envio", "fecha_entrega", "fecha_notificacion", "abogado_responsable"];

const hoyISO = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};

function textoPlazo(c) {
  if (c.fecha_limite_comparecencia) {
    const d = c.dias_restantes;
    const cuando = d === null ? "" : d < 0 ? ` (vencido hace ${-d} d)` : d === 0 ? " (vence hoy)" : ` (faltan ${d} d)`;
    return { texto: `Comparecer hasta ${fecha(c.fecha_limite_comparecencia)}${cuando}`, color: d !== null && d < 0 ? "#c73a3a" : "#1f3b57" };
  }
  if (c.fecha_surte_efecto) return { texto: `Surte efecto el ${fecha(c.fecha_surte_efecto)}`, color: "#1f3b57" };
  return null;
}

export default function Citaciones() {
  const [lista, setLista] = useState([]);
  const [demandas, setDemandas] = useState([]);
  const [expedientes, setExpedientes] = useState([]);
  const [usuarios, setUsuarios] = useState([]);
  const [perfil, setPerfil] = useState(null);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(true);
  const [busqueda, setBusqueda] = useState("");
  const [filtro, setFiltro] = useState(null);
  const [form, setForm] = useState(null);
  const [editandoId, setEditandoId] = useState(null);
  const [formError, setFormError] = useState("");
  const [guardando, setGuardando] = useState(false);
  const [detalle, setDetalle] = useState(null);

  const cargar = () => {
    setCargando(true);
    api
      .get("/citaciones/")
      .then((r) => setLista(r.data))
      .catch((err) => setError(mensajeError(err, "No se pudieron cargar las citaciones.")))
      .finally(() => setCargando(false));
  };

  useEffect(() => {
    cargar();
    api.get("/demandas/").then((r) => setDemandas(r.data)).catch(() => {});
    api.get("/expedientes/").then((r) => setExpedientes(r.data)).catch(() => {});
    api.get("/usuarios/").then((r) => setUsuarios(r.data)).catch(() => {});
    api.get("/perfil/").then((r) => setPerfil(r.data)).catch(() => {});
  }, []);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const abrirNueva = () => { setForm({ ...VACIO }); setEditandoId(null); setFormError(""); };
  const abrirEditar = (c) => {
    setForm({
      destinatario: c.destinatario, direccion: c.direccion || "", tipo: c.tipo, ubicacion: c.ubicacion, estado: c.estado,
      demanda: c.demanda || "", expediente: c.expediente || "", fecha_envio: c.fecha_envio || "", empresa_mensajeria: c.empresa_mensajeria || "",
      guia: c.guia || "", fecha_entrega: c.fecha_entrega || "", fecha_notificacion: c.fecha_notificacion || "",
      abogado_responsable: c.abogado_responsable || "", observaciones: c.observaciones || "",
    });
    setEditandoId(c.id);
    setFormError("");
  };

  const guardar = async (e) => {
    e.preventDefault();
    setFormError("");
    setGuardando(true);
    try {
      const datos = { ...form };
      NULABLES.forEach((k) => { if (datos[k] === "") { if (editandoId) datos[k] = null; else delete datos[k]; } });
      if (editandoId) await api.patch(`/citaciones/${editandoId}/`, datos);
      else await api.post("/citaciones/", datos);
      setForm(null);
      setEditandoId(null);
      cargar();
    } catch (err) {
      setFormError(mensajeError(err, "No se pudo guardar la citación."));
    } finally {
      setGuardando(false);
    }
  };

  const eliminar = async (c) => {
    if (!window.confirm("¿Eliminar este registro? Esta acción no se puede deshacer.")) return;
    try {
      await api.delete(`/citaciones/${c.id}/`);
      cargar();
    } catch (err) {
      alert(mensajeError(err, "No se pudo eliminar."));
    }
  };

  const conteo = (est) => lista.filter((c) => c.estado === est).length;
  const vencidas = lista.filter((c) => c.dias_restantes !== null && c.dias_restantes < 0).length;
  const visibles = lista.filter((c) => {
    const t = busqueda.toLowerCase();
    const coincide = [c.destinatario, c.direccion || "", c.guia || "", c.demanda_texto || ""].some((x) => x.toLowerCase().includes(t));
    return coincide && (!filtro || c.estado === filtro);
  });

  const mostrarEnvio = form && form.estado !== "pendiente";
  const mostrarEntrega = form && ["entregada", "notificado"].includes(form.estado);

  return (
    <Layout>
      <div style={{ minHeight: "100vh", background: "#f4f7fb", fontFamily: "sans-serif" }}>
        <Encabezado Icono={Send} titulo="Citación de demanda" busqueda={busqueda} setBusqueda={setBusqueda} placeholder="Buscar citación..." textoBoton="+ Nueva citación" onNuevo={abrirNueva} />
        <main style={{ padding: "32px" }}>
          <p style={{ color: "#6b7f96", fontSize: "13px", marginTop: 0 }}>
            Control de la notificación al demandado: citación para notificación personal (art. 291 CGP) y, si no comparece, notificación por aviso (art. 292 CGP).
            El plazo para comparecer se calcula en días hábiles desde la entrega de la citación. Verifique siempre las fechas con la constancia de la empresa de mensajería.
          </p>
          {error && <p style={{ color: "#c73a3a" }}>{error}</p>}
          {cargando && <p>Cargando...</p>}
          {!cargando && !error && (
            <>
              <div style={{ display: "flex", gap: "10px", marginBottom: "20px", flexWrap: "wrap" }}>
                <Chip label={`Todas (${lista.length})`} activo={!filtro} onClick={() => setFiltro(null)} />
                {Object.entries(ESTADOS).map(([k, v]) => (
                  <Chip key={k} label={`${v.label} (${conteo(k)})`} activo={filtro === k} onClick={() => setFiltro(filtro === k ? null : k)} bg={v.bg} color={v.color} />
                ))}
              </div>
              {vencidas > 0 && (
                <p style={{ background: "#fde8e8", color: "#c73a3a", padding: "10px 14px", borderRadius: "10px", fontSize: "14px" }}>
                  ⚠ {vencidas} citación(es) con el plazo de comparecencia vencido: corresponde enviar la notificación por aviso.
                </p>
              )}
              <div style={{ background: "white", borderRadius: "16px", border: "1px solid #eef2f6", overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
                  <thead>
                    <tr style={{ background: "#f8fafc" }}>
                      {["Destinatario", "Tipo", "Envío / guía", "Plazo", "Estado", "Responsable", "Acción"].map((h) => <th key={h} style={thStyle}>{h}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {visibles.map((c) => {
                      const est = ESTADOS[c.estado] || ESTADOS.pendiente;
                      const plazo = textoPlazo(c);
                      return (
                        <tr key={c.id} style={{ borderTop: "1px solid #f0f3f8" }}>
                          <td style={tdStyle}>
                            <strong>{c.destinatario}</strong>
                            <div style={{ color: "#6b7f96", fontSize: "12px" }}>{c.demanda_texto || c.expediente_numero || "Sin demanda asociada"}</div>
                          </td>
                          <td style={tdStyle}>{TIPOS[c.tipo]}</td>
                          <td style={tdStyle}>
                            {fecha(c.fecha_envio)}
                            {c.guia && <div style={{ color: "#6b7f96", fontSize: "12px" }}>{c.empresa_mensajeria} · guía {c.guia}</div>}
                          </td>
                          <td style={tdStyle}>{plazo ? <span style={{ color: plazo.color, fontWeight: 600 }}>{plazo.texto}</span> : "—"}</td>
                          <td style={tdStyle}><Etiqueta texto={est.label} bg={est.bg} color={est.color} /></td>
                          <td style={tdStyle}>{c.abogado_nombre || "—"}</td>
                          <td style={tdStyle}>
                            <button style={enlace()} onClick={() => setDetalle(c)}>Ver</button>
                            <button style={enlace("#a8681a")} onClick={() => abrirEditar(c)}>Editar</button>
                            <button style={enlace("#c73a3a")} onClick={() => eliminar(c)}>Eliminar</button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                {visibles.length === 0 && (
                  <p style={{ padding: "24px", color: "#6b7f96" }}>{lista.length === 0 ? "Aún no hay citaciones registradas." : "No hay citaciones que coincidan."}</p>
                )}
              </div>
            </>
          )}
        </main>

        {form && (
          <Modal onClose={() => setForm(null)} comoFormulario onSubmit={guardar} ancho={580}>
            <h2 style={{ marginTop: 0 }}>{editandoId ? "✏️ Editar citación" : "+ Nueva citación"}</h2>
            {formError && <p style={mensajeErrorEstilo}>{formError}</p>}
            <Campo label="Destinatario (demandado a notificar)"><input value={form.destinatario} onChange={set("destinatario")} required style={inputStyle} /></Campo>
            <Campo label="Dirección de notificación"><input value={form.direccion} onChange={set("direccion")} style={inputStyle} /></Campo>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 14px" }}>
              <Campo label="Tipo">
                <select value={form.tipo} onChange={set("tipo")} style={inputStyle}>
                  {Object.entries(TIPOS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
              </Campo>
              <Campo label="Estado">
                <select value={form.estado} onChange={set("estado")} style={inputStyle}>
                  {Object.entries(ESTADOS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
                </select>
              </Campo>
            </div>
            {form.tipo === "citacion" && (
              <Campo label="Ubicación del destinatario (define el plazo para comparecer)">
                <select value={form.ubicacion} onChange={set("ubicacion")} style={inputStyle}>
                  {Object.entries(UBICACIONES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
              </Campo>
            )}
            {mostrarEnvio && (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 14px" }}>
                <Campo label="Fecha de envío"><input type="date" max={hoyISO()} value={form.fecha_envio} onChange={set("fecha_envio")} style={inputStyle} /></Campo>
                <Campo label="Empresa de mensajería"><input value={form.empresa_mensajeria} onChange={set("empresa_mensajeria")} style={inputStyle} /></Campo>
                <Campo label="Número de guía"><input value={form.guia} onChange={set("guia")} style={inputStyle} /></Campo>
                {mostrarEntrega && <Campo label="Fecha de entrega"><input type="date" max={hoyISO()} value={form.fecha_entrega} onChange={set("fecha_entrega")} style={inputStyle} /></Campo>}
                {form.estado === "notificado" && <Campo label="Fecha de notificación"><input type="date" max={hoyISO()} value={form.fecha_notificacion} onChange={set("fecha_notificacion")} style={inputStyle} /></Campo>}
              </div>
            )}
            <Campo label="Demanda asociada">
              <select value={form.demanda} onChange={set("demanda")} style={inputStyle}>
                <option value="">Sin demanda</option>
                {demandas.map((d) => <option key={d.id} value={d.id}>{d.clase_proceso}: {d.demandante} vs {d.demandado}</option>)}
              </select>
            </Campo>
            <Campo label="Expediente">
              <select value={form.expediente} onChange={set("expediente")} style={inputStyle}>
                <option value="">Sin expediente</option>
                {expedientes.map((x) => <option key={x.id} value={x.id}>{x.numero} · {x.demandante}</option>)}
              </select>
            </Campo>
            {perfil?.es_directivo && (
              <Campo label="Abogado responsable">
                <select value={form.abogado_responsable} onChange={set("abogado_responsable")} style={inputStyle}>
                  <option value="">Yo (por defecto)</option>
                  {usuarios.map((u) => <option key={u.id} value={u.id}>{u.nombre_completo}</option>)}
                </select>
              </Campo>
            )}
            <Campo label="Observaciones"><textarea rows={2} value={form.observaciones} onChange={set("observaciones")} style={inputStyle} /></Campo>
            <div style={{ display: "flex", gap: "10px", marginTop: "20px" }}>
              <button type="button" onClick={() => setForm(null)} style={{ ...botonSecundario, flex: 1 }}>Cancelar</button>
              <button type="submit" disabled={guardando} style={{ flex: 1, padding: "10px", borderRadius: "8px", border: "none", background: "#0a1a2b", color: "white", cursor: "pointer" }}>
                {guardando ? "Guardando..." : "Guardar"}
              </button>
            </div>
          </Modal>
        )}

        {detalle && (
          <Modal onClose={() => setDetalle(null)} ancho={560}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h2 style={{ margin: 0, fontSize: "18px" }}>{TIPOS[detalle.tipo]}</h2>
              <span onClick={() => setDetalle(null)} style={{ cursor: "pointer", fontSize: "22px" }}>&times;</span>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px", margin: "16px 0" }}>
              <Dato label="Destinatario" value={detalle.destinatario} />
              <Dato label="Dirección" value={detalle.direccion} />
              <Dato label="Estado" value={detalle.estado_display} />
              <Dato label="Ubicación" value={detalle.tipo === "citacion" ? detalle.ubicacion_display : "—"} />
              <Dato label="Envío" value={fecha(detalle.fecha_envio)} />
              <Dato label="Mensajería / guía" value={[detalle.empresa_mensajeria, detalle.guia].filter(Boolean).join(" · ")} />
              <Dato label="Entrega" value={fecha(detalle.fecha_entrega)} />
              <Dato label="Notificado" value={fecha(detalle.fecha_notificacion)} />
              <Dato label="Plazo" value={textoPlazo(detalle)?.texto} />
              <Dato label="Responsable" value={detalle.abogado_nombre} />
              <Dato label="Demanda" value={detalle.demanda_texto} />
              <Dato label="Expediente" value={detalle.expediente_numero} />
            </div>
            {detalle.observaciones && <Dato label="Observaciones" value={<span style={{ whiteSpace: "pre-line" }}>{detalle.observaciones}</span>} />}
          </Modal>
        )}
      </div>
    </Layout>
  );
}
