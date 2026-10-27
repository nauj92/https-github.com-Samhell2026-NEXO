import { useEffect, useState } from "react";
import { FileText } from "lucide-react";
import api from "../api";
import Layout from "../components/Layout";
import { mensajeError } from "../utils/errores";
import { fecha, limpiar, pesos } from "../utils/formato";
import Borrador from "../components/Borrador";
import { Encabezado, Modal, Campo, Dato, Chip, Etiqueta, inputStyle, thStyle, tdStyle, botonSecundario, enlace, mensajeErrorEstilo } from "../components/ui";

const ESTADOS = {
  elaboracion: { label: "En elaboración", bg: "#e9ecf0", color: "#5b6f84" },
  radicada: { label: "Radicada", bg: "#e3effa", color: "#2a6aa8" },
  inadmitida: { label: "Inadmitida (subsanar)", bg: "#fff3d6", color: "#a8681a" },
  admitida: { label: "Admitida", bg: "#e2f3e8", color: "#1b8b5e" },
  rechazada: { label: "Rechazada", bg: "#fde8e8", color: "#c73a3a" },
  retirada: { label: "Retirada", bg: "#eee", color: "#777" },
};

// Campos de los requisitos del artículo 82 del Código General del Proceso (con su valor inicial)
const ART82 = {
  juez_destinatario: "",
  demandante_tipo_persona: "natural", demandante_tipo_documento: "CC", demandante_documento: "", demandante_domicilio: "",
  demandante_representante: "", demandante_representante_documento: "",
  demandado_tipo_persona: "natural", demandado_tipo_documento: "", demandado_documento: "", demandado_domicilio: "",
  demandado_representante: "", demandado_ubicacion_desconocida: false, otras_partes: "",
  sin_apoderado: false, apoderado_nombre: "", apoderado_documento: "", apoderado_tarjeta_profesional: "",
  hechos: [""], pruebas: "", documentos_en_poder_demandado: "",
  requiere_juramento_estimatorio: false, juramento_estimatorio: "", fundamentos_derecho: "", cuantia_aplica: true,
  notif_demandante_direccion: "", notif_demandante_email: "", notif_demandado_direccion: "", notif_demandado_email: "",
  notif_apoderado_direccion: "", notif_apoderado_email: "", otros_requisitos: "",
};

const VACIO = {
  clase_proceso: "", cliente: "", expediente: "", juzgado: "", demandante: "", demandado: "", pretensiones: "",
  cuantia: "", estado: "elaboracion", fecha_radicacion: "", fecha_inadmision: "", fecha_admision: "",
  abogado_responsable: "", observaciones: "", ...ART82,
};

const TIPOS_PERSONA = [["natural", "Persona natural"], ["juridica", "Persona jurídica / patrimonio autónomo"]];
const TIPOS_DOC = [["CC", "Cédula de ciudadanía"], ["CE", "Cédula de extranjería"], ["NIT", "NIT"], ["PAS", "Pasaporte"]];

function Seccion({ numero, titulo, ayuda, children }) {
  return (
    <section style={{ border: "1px solid #e9edf2", borderRadius: "12px", padding: "14px 16px", marginBottom: "14px", background: "#fcfdfe" }}>
      <div style={{ fontWeight: 700, color: "#0a1a2b", marginBottom: ayuda ? "2px" : "10px" }}>
        {numero && <span style={{ color: "#a8681a" }}>{numero}. </span>}
        {titulo}
      </div>
      {ayuda && <div style={{ fontSize: "12px", color: "#6b7f96", marginBottom: "10px" }}>{ayuda}</div>}
      {children}
    </section>
  );
}

const dosCol = { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 14px" };

function Casilla({ checked, onChange, children }) {
  return (
    <label style={{ fontSize: "14px", display: "flex", gap: "8px", alignItems: "center", margin: "6px 0 12px" }}>
      <input type="checkbox" checked={checked} onChange={onChange} />
      {children}
    </label>
  );
}

function ChipRequisitos({ req }) {
  if (!req) return "—";
  const ok = req.cumplidos === req.total;
  return (
    <Etiqueta
      texto={`${req.cumplidos}/${req.total}`}
      bg={ok ? "#e2f3e8" : req.cumplidos >= req.total - 3 ? "#fff3d6" : "#fde8e8"}
      color={ok ? "#1b8b5e" : req.cumplidos >= req.total - 3 ? "#a8681a" : "#c73a3a"}
    />
  );
}

const hoyISO = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};

function textoSubsanacion(d) {
  if (!d.fecha_limite_subsanacion) return null;
  const dias = d.dias_para_subsanar;
  const cuando = dias < 0 ? `vencido hace ${-dias} d` : dias === 0 ? "vence hoy" : `faltan ${dias} d`;
  return { texto: `${fecha(d.fecha_limite_subsanacion)} (${cuando})`, color: dias < 0 ? "#c73a3a" : dias <= 2 ? "#a8681a" : "#1b8b5e" };
}

export default function Demandas() {
  const [demandas, setDemandas] = useState([]);
  const [clientes, setClientes] = useState([]);
  const [juzgados, setJuzgados] = useState([]);
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
      .get("/demandas/")
      .then((r) => setDemandas(r.data))
      .catch((err) => setError(mensajeError(err, "No se pudieron cargar las demandas.")))
      .finally(() => setCargando(false));
  };

  useEffect(() => {
    cargar();
    api.get("/clientes/").then((r) => setClientes(r.data)).catch(() => {});
    api.get("/juzgados/").then((r) => setJuzgados(r.data)).catch(() => {});
    api.get("/expedientes/").then((r) => setExpedientes(r.data)).catch(() => {});
    api.get("/usuarios/").then((r) => setUsuarios(r.data)).catch(() => {});
    api.get("/perfil/").then((r) => setPerfil(r.data)).catch(() => {});
  }, []);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const abrirNueva = () => {
    setForm({ ...VACIO });
    setEditandoId(null);
    setFormError("");
  };
  const abrirEditar = (d) => {
    const art82 = Object.fromEntries(Object.entries(ART82).map(([k, v]) => [k, d[k] ?? v]));
    if (!art82.hechos.length) art82.hechos = [""];
    setForm({
      clase_proceso: d.clase_proceso, cliente: d.cliente || "", expediente: d.expediente || "", juzgado: d.juzgado || "",
      demandante: d.demandante, demandado: d.demandado, pretensiones: d.pretensiones, cuantia: d.cuantia,
      estado: d.estado, fecha_radicacion: d.fecha_radicacion || "", fecha_inadmision: d.fecha_inadmision || "",
      fecha_admision: d.fecha_admision || "", abogado_responsable: d.abogado_responsable || "", observaciones: d.observaciones || "",
      ...art82,
    });
    setEditandoId(d.id);
    setFormError("");
  };

  const setCheck = (k) => (e) => setForm({ ...form, [k]: e.target.checked });
  const setHecho = (i, v) => setForm({ ...form, hechos: form.hechos.map((h, j) => (j === i ? v : h)) });
  const agregarHecho = () => setForm({ ...form, hechos: [...form.hechos, ""] });
  const quitarHecho = (i) => {
    const resto = form.hechos.filter((_, j) => j !== i);
    setForm({ ...form, hechos: resto.length ? resto : [""] });
  };

  const guardar = async (e) => {
    e.preventDefault();
    setFormError("");
    setGuardando(true);
    try {
      const base = { ...form, cuantia: form.cuantia === "" ? "0" : form.cuantia };
      // En edición, los campos vacíos se envían como null para poder borrar una fecha o un vínculo
      const nulables = ["cliente", "expediente", "juzgado", "fecha_radicacion", "fecha_inadmision", "fecha_admision", "abogado_responsable"];
      let datos;
      if (editandoId) {
        datos = { ...base };
        nulables.forEach((k) => { if (datos[k] === "") datos[k] = null; });
      } else {
        datos = limpiar(base);
      }
      datos.hechos = (datos.hechos || []).filter((h) => h.trim());
      const r = editandoId ? await api.patch(`/demandas/${editandoId}/`, datos) : await api.post("/demandas/", datos);
      setForm(null);
      setEditandoId(null);
      cargar();
      // Si la demanda ya salió de "en elaboración", se avisa qué numerales del art. 82 faltan
      const req = r.data.requisitos;
      if (r.data.estado !== "elaboracion" && req && req.cumplidos < req.total) {
        const faltas = req.items.filter((x) => x.cumple === false).map((x) => `${x.numeral}. ${x.titulo}`).join("\n");
        alert(`La demanda se guardó, pero aún no cumple todos los requisitos del artículo 82 del CGP (${req.cumplidos}/${req.total}). Falta:\n\n${faltas}`);
      }
    } catch (err) {
      setFormError(mensajeError(err, "No se pudo guardar la demanda."));
    } finally {
      setGuardando(false);
    }
  };

  const eliminar = async (d) => {
    if (!window.confirm("¿Eliminar esta demanda? Esta acción no se puede deshacer.")) return;
    try {
      await api.delete(`/demandas/${d.id}/`);
      cargar();
    } catch (err) {
      alert(mensajeError(err, "No se pudo eliminar la demanda."));
    }
  };

  const conteo = (est) => demandas.filter((d) => d.estado === est).length;
  const porSubsanar = demandas.filter((d) => d.estado === "inadmitida" && d.dias_para_subsanar !== null && d.dias_para_subsanar <= 2).length;

  const visibles = demandas.filter((d) => {
    const t = busqueda.toLowerCase();
    const coincide = [d.demandante, d.demandado, d.clase_proceso, d.cliente_nombre || ""].some((x) => x.toLowerCase().includes(t));
    return coincide && (!filtro || d.estado === filtro);
  });

  const mostrarRadicacion = form && ["radicada", "inadmitida", "admitida", "rechazada"].includes(form.estado);

  return (
    <Layout>
      <div style={{ minHeight: "100vh", background: "#f4f7fb", fontFamily: "sans-serif" }}>
        <Encabezado Icono={FileText} titulo="A1 · Elaboración de demanda" busqueda={busqueda} setBusqueda={setBusqueda} placeholder="Buscar demanda..." textoBoton="+ Nueva demanda" onNuevo={abrirNueva} />
        <main style={{ padding: "32px" }}>
          {error && <p style={{ color: "#c73a3a" }}>{error}</p>}
          {cargando && <p>Cargando...</p>}
          {!cargando && !error && (
            <>
              <div style={{ display: "flex", gap: "10px", marginBottom: "20px", flexWrap: "wrap" }}>
                <Chip label={`Todas (${demandas.length})`} activo={!filtro} onClick={() => setFiltro(null)} />
                {Object.entries(ESTADOS).map(([k, v]) => (
                  <Chip key={k} label={`${v.label} (${conteo(k)})`} activo={filtro === k} onClick={() => setFiltro(filtro === k ? null : k)} bg={v.bg} color={v.color} />
                ))}
              </div>
              {porSubsanar > 0 && (
                <p style={{ background: "#fff3d6", color: "#a8681a", padding: "10px 14px", borderRadius: "10px", fontSize: "14px" }}>
                  ⚠ {porSubsanar} demanda(s) inadmitida(s) con el plazo de subsanación por vencer o vencido.
                </p>
              )}
              <div style={{ background: "white", borderRadius: "16px", border: "1px solid #eef2f6", overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
                  <thead>
                    <tr style={{ background: "#f8fafc" }}>
                      {["Proceso", "Partes", "Cuantía", "Art. 82", "Estado", "Subsanar hasta", "Responsable", "Acción"].map((h) => (
                        <th key={h} style={thStyle}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {visibles.map((d) => {
                      const est = ESTADOS[d.estado] || ESTADOS.elaboracion;
                      const sub = textoSubsanacion(d);
                      return (
                        <tr key={d.id} style={{ borderTop: "1px solid #f0f3f8" }}>
                          <td style={tdStyle}>
                            <strong>{d.clase_proceso}</strong>
                            <div style={{ color: "#6b7f96", fontSize: "12px" }}>{d.expediente_numero || "Sin expediente"}</div>
                          </td>
                          <td style={tdStyle}>{d.demandante} <span style={{ color: "#6b7f96" }}>vs</span> {d.demandado}</td>
                          <td style={tdStyle}>{pesos(d.cuantia)}</td>
                          <td style={tdStyle}><ChipRequisitos req={d.requisitos} /></td>
                          <td style={tdStyle}><Etiqueta texto={est.label} bg={est.bg} color={est.color} /></td>
                          <td style={tdStyle}>{sub ? <span style={{ color: sub.color, fontWeight: 600 }}>{sub.texto}</span> : "—"}</td>
                          <td style={tdStyle}>{d.abogado_nombre || "—"}</td>
                          <td style={tdStyle}>
                            <button style={enlace()} onClick={() => setDetalle(d)}>Ver</button>
                            <button style={enlace("#a8681a")} onClick={() => abrirEditar(d)}>Editar</button>
                            <button style={enlace("#c73a3a")} onClick={() => eliminar(d)}>Eliminar</button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                {visibles.length === 0 && (
                  <p style={{ padding: "24px", color: "#6b7f96" }}>{demandas.length === 0 ? "Aún no hay demandas registradas." : "No hay demandas que coincidan."}</p>
                )}
              </div>
            </>
          )}
        </main>

        {form && (
          <Modal onClose={() => setForm(null)} comoFormulario onSubmit={guardar} ancho={860}>
            <h2 style={{ marginTop: 0 }}>{editandoId ? "✏️ Editar demanda" : "+ Nueva demanda"}</h2>
            <p style={{ fontSize: "13px", color: "#6b7f96", marginTop: 0 }}>
              El formulario sigue los requisitos del artículo 82 del Código General del Proceso. Puede guardar la demanda incompleta y terminarla después;
              el sistema le indica qué numerales faltan.
            </p>
            {formError && <p style={mensajeErrorEstilo}>{formError}</p>}

            <Seccion titulo="Datos generales">
              <Campo label="Clase de proceso">
                <input value={form.clase_proceso} onChange={set("clase_proceso")} required placeholder="Ej.: Ejecutivo singular, Ordinario laboral" style={inputStyle} />
              </Campo>
              <div style={dosCol}>
                <Campo label="Estado">
                  <select value={form.estado} onChange={set("estado")} style={inputStyle}>
                    {Object.entries(ESTADOS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
                  </select>
                </Campo>
                <Campo label="Cliente">
                  <select value={form.cliente} onChange={set("cliente")} style={inputStyle}>
                    <option value="">Sin cliente</option>
                    {clientes.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
                  </select>
                </Campo>
                <Campo label="Juzgado">
                  <select value={form.juzgado} onChange={set("juzgado")} style={inputStyle}>
                    <option value="">Sin asignar</option>
                    {juzgados.map((j) => <option key={j.id} value={j.id}>{j.nombre}</option>)}
                  </select>
                </Campo>
                <Campo label="Expediente (cuando ya exista)">
                  <select value={form.expediente} onChange={set("expediente")} style={inputStyle}>
                    <option value="">Sin expediente</option>
                    {expedientes.map((x) => <option key={x.id} value={x.id}>{x.numero} · {x.demandante}</option>)}
                  </select>
                </Campo>
              </div>
              {mostrarRadicacion && (
                <div style={dosCol}>
                  <Campo label="Fecha de radicación"><input type="date" max={hoyISO()} value={form.fecha_radicacion} onChange={set("fecha_radicacion")} style={inputStyle} /></Campo>
                  {form.estado === "inadmitida" && (
                    <Campo label="Fecha del auto que inadmite" ayuda="El plazo de 5 días hábiles para subsanar se calcula solo.">
                      <input type="date" value={form.fecha_inadmision} onChange={set("fecha_inadmision")} style={inputStyle} />
                    </Campo>
                  )}
                  {form.estado === "admitida" && (
                    <Campo label="Fecha del auto admisorio"><input type="date" value={form.fecha_admision} onChange={set("fecha_admision")} style={inputStyle} /></Campo>
                  )}
                </div>
              )}
              {perfil?.es_directivo && (
                <Campo label="Abogado responsable en el sistema">
                  <select value={form.abogado_responsable} onChange={set("abogado_responsable")} style={inputStyle}>
                    <option value="">Yo (por defecto)</option>
                    {usuarios.map((u) => <option key={u.id} value={u.id}>{u.nombre_completo}</option>)}
                  </select>
                </Campo>
              )}
            </Seccion>

            <Seccion numero="1" titulo="Juez a quien se dirige la demanda">
              <Campo label="Designación del juez o despacho" ayuda="Si deja este campo vacío se usa el juzgado seleccionado arriba.">
                <input value={form.juez_destinatario} onChange={set("juez_destinatario")} placeholder="Ej.: Juez Civil del Circuito de Cali (Reparto)" style={inputStyle} />
              </Campo>
            </Seccion>

            <Seccion numero="2" titulo="Partes: nombre, domicilio e identificación" ayuda="Si no pueden comparecer por sí mismas, indique su representante legal. Las personas jurídicas se identifican con NIT. El documento del demandado es opcional (si se conoce).">
              <div style={dosCol}>
                <div>
                  <div style={{ fontWeight: 600, marginBottom: "8px" }}>Demandante</div>
                  <Campo label="Nombre o razón social"><input value={form.demandante} onChange={set("demandante")} required style={inputStyle} /></Campo>
                  <Campo label="Tipo de persona">
                    <select value={form.demandante_tipo_persona} onChange={(e) => setForm({ ...form, demandante_tipo_persona: e.target.value, demandante_tipo_documento: e.target.value === "juridica" ? "NIT" : form.demandante_tipo_documento === "NIT" ? "CC" : form.demandante_tipo_documento })} style={inputStyle}>
                      {TIPOS_PERSONA.map(([v, t]) => <option key={v} value={v}>{t}</option>)}
                    </select>
                  </Campo>
                  <div style={dosCol}>
                    <Campo label="Tipo de documento">
                      <select value={form.demandante_tipo_documento} onChange={set("demandante_tipo_documento")} disabled={form.demandante_tipo_persona === "juridica"} style={inputStyle}>
                        <option value="">Seleccione</option>
                        {TIPOS_DOC.map(([v, t]) => <option key={v} value={v}>{t}</option>)}
                      </select>
                    </Campo>
                    <Campo label="Número"><input value={form.demandante_documento} onChange={set("demandante_documento")} placeholder={form.demandante_tipo_persona === "juridica" ? "900123456-7" : "Sin puntos"} style={inputStyle} /></Campo>
                  </div>
                  <Campo label="Domicilio"><input value={form.demandante_domicilio} onChange={set("demandante_domicilio")} placeholder="Ciudad y departamento" style={inputStyle} /></Campo>
                  <Campo label="Representante legal (si aplica)"><input value={form.demandante_representante} onChange={set("demandante_representante")} style={inputStyle} /></Campo>
                  <Campo label="Documento del representante"><input value={form.demandante_representante_documento} onChange={set("demandante_representante_documento")} placeholder="Ej.: C.C. 12345678" style={inputStyle} /></Campo>
                </div>
                <div>
                  <div style={{ fontWeight: 600, marginBottom: "8px" }}>Demandado</div>
                  <Campo label="Nombre o razón social"><input value={form.demandado} onChange={set("demandado")} required style={inputStyle} /></Campo>
                  <Campo label="Tipo de persona">
                    <select value={form.demandado_tipo_persona} onChange={(e) => setForm({ ...form, demandado_tipo_persona: e.target.value, demandado_tipo_documento: e.target.value === "juridica" ? "NIT" : form.demandado_tipo_documento === "NIT" ? "CC" : form.demandado_tipo_documento })} style={inputStyle}>
                      {TIPOS_PERSONA.map(([v, t]) => <option key={v} value={v}>{t}</option>)}
                    </select>
                  </Campo>
                  <div style={dosCol}>
                    <Campo label="Tipo de documento">
                      <select value={form.demandado_tipo_documento} onChange={set("demandado_tipo_documento")} disabled={form.demandado_tipo_persona === "juridica"} style={inputStyle}>
                        <option value="">No se conoce</option>
                        {TIPOS_DOC.map(([v, t]) => <option key={v} value={v}>{t}</option>)}
                      </select>
                    </Campo>
                    <Campo label="Número (si se conoce)"><input value={form.demandado_documento} onChange={set("demandado_documento")} style={inputStyle} /></Campo>
                  </div>
                  <Campo label="Domicilio"><input value={form.demandado_domicilio} onChange={set("demandado_domicilio")} disabled={form.demandado_ubicacion_desconocida} placeholder="Ciudad y departamento" style={inputStyle} /></Campo>
                  <Campo label="Representante legal (si aplica)"><input value={form.demandado_representante} onChange={set("demandado_representante")} style={inputStyle} /></Campo>
                  <Casilla checked={form.demandado_ubicacion_desconocida} onChange={setCheck("demandado_ubicacion_desconocida")}>
                    Se desconoce el domicilio del demandado o el lugar donde recibirá notificaciones (parágrafo 1)
                  </Casilla>
                </div>
              </div>
              <Campo label="Otras partes (si hay más demandantes o demandados)">
                <textarea rows={2} value={form.otras_partes} onChange={set("otras_partes")} placeholder="Nombre, identificación y domicilio de cada una" style={inputStyle} />
              </Campo>
            </Seccion>

            <Seccion numero="3" titulo="Apoderado judicial del demandante">
              <Casilla checked={form.sin_apoderado} onChange={setCheck("sin_apoderado")}>El demandante actúa sin apoderado judicial</Casilla>
              {!form.sin_apoderado && (
                <div style={dosCol}>
                  <Campo label="Nombre del apoderado"><input value={form.apoderado_nombre} onChange={set("apoderado_nombre")} style={inputStyle} /></Campo>
                  <Campo label="Cédula (C.C.)"><input value={form.apoderado_documento} onChange={set("apoderado_documento")} style={inputStyle} /></Campo>
                  <Campo label="Tarjeta profesional (T.P.)"><input value={form.apoderado_tarjeta_profesional} onChange={set("apoderado_tarjeta_profesional")} style={inputStyle} /></Campo>
                </div>
              )}
            </Seccion>

            <Seccion numero="4" titulo="Pretensiones" ayuda="Lo que se pretende, expresado con precisión y claridad.">
              <textarea rows={4} value={form.pretensiones} onChange={set("pretensiones")} required placeholder="Mínimo 10 caracteres" style={inputStyle} />
            </Seccion>

            <Seccion numero="5" titulo="Hechos" ayuda="Debidamente determinados, clasificados y numerados. El sistema los numera en el escrito.">
              {form.hechos.map((h, i) => (
                <div key={i} style={{ display: "grid", gridTemplateColumns: "28px 1fr 24px", gap: "8px", marginBottom: "8px", alignItems: "start" }}>
                  <strong style={{ paddingTop: "8px" }}>{i + 1}.</strong>
                  <textarea rows={2} value={h} onChange={(e) => setHecho(i, e.target.value)} style={inputStyle} />
                  <button type="button" onClick={() => quitarHecho(i)} title="Quitar" style={{ border: "none", background: "none", color: "#c73a3a", cursor: "pointer", paddingTop: "6px" }}>✕</button>
                </div>
              ))}
              <button type="button" onClick={agregarHecho} style={botonSecundario}>+ Agregar hecho</button>
            </Seccion>

            <Seccion numero="6" titulo="Pruebas">
              <Campo label="Pruebas que se pretende hacer valer"><textarea rows={3} value={form.pruebas} onChange={set("pruebas")} style={inputStyle} /></Campo>
              <Campo label="Documentos que el demandado tiene en su poder (para que los aporte)"><textarea rows={2} value={form.documentos_en_poder_demandado} onChange={set("documentos_en_poder_demandado")} style={inputStyle} /></Campo>
            </Seccion>

            <Seccion numero="7" titulo="Juramento estimatorio">
              <Casilla checked={form.requiere_juramento_estimatorio} onChange={setCheck("requiere_juramento_estimatorio")}>Es necesario en esta demanda</Casilla>
              {form.requiere_juramento_estimatorio && (
                <textarea rows={3} value={form.juramento_estimatorio} onChange={set("juramento_estimatorio")} placeholder="Estimación razonada y bajo juramento, discriminando cada concepto" style={inputStyle} />
              )}
            </Seccion>

            <Seccion numero="8" titulo="Fundamentos de derecho">
              <textarea rows={3} value={form.fundamentos_derecho} onChange={set("fundamentos_derecho")} placeholder="Normas sustanciales y procesales aplicables" style={inputStyle} />
            </Seccion>

            <Seccion numero="9" titulo="Cuantía del proceso">
              <Casilla checked={form.cuantia_aplica} onChange={setCheck("cuantia_aplica")}>Su estimación es necesaria para determinar la competencia o el trámite</Casilla>
              {form.cuantia_aplica && (
                <Campo label="Cuantía (COP)"><input type="number" min="0" step="1" value={form.cuantia} onChange={set("cuantia")} style={inputStyle} /></Campo>
              )}
            </Seccion>

            <Seccion numero="10" titulo="Lugar y direcciones para notificaciones" ayuda="Dirección física y electrónica donde las partes, sus representantes y el apoderado recibirán notificaciones personales.">
              <div style={dosCol}>
                <Campo label="Demandante: dirección física"><input value={form.notif_demandante_direccion} onChange={set("notif_demandante_direccion")} style={inputStyle} /></Campo>
                <Campo label="Demandante: correo electrónico"><input type="email" value={form.notif_demandante_email} onChange={set("notif_demandante_email")} style={inputStyle} /></Campo>
                {!form.sin_apoderado && (
                  <>
                    <Campo label="Apoderado: dirección física"><input value={form.notif_apoderado_direccion} onChange={set("notif_apoderado_direccion")} style={inputStyle} /></Campo>
                    <Campo label="Apoderado: correo electrónico"><input type="email" value={form.notif_apoderado_email} onChange={set("notif_apoderado_email")} style={inputStyle} /></Campo>
                  </>
                )}
                {!form.demandado_ubicacion_desconocida && (
                  <>
                    <Campo label="Demandado: dirección física"><input value={form.notif_demandado_direccion} onChange={set("notif_demandado_direccion")} style={inputStyle} /></Campo>
                    <Campo label="Demandado: correo electrónico"><input type="email" value={form.notif_demandado_email} onChange={set("notif_demandado_email")} style={inputStyle} /></Campo>
                  </>
                )}
              </div>
              {form.demandado_ubicacion_desconocida && <p style={{ fontSize: "12px", color: "#6b7f96", margin: 0 }}>Se expresará en el escrito que se desconoce el lugar de notificación del demandado.</p>}
            </Seccion>

            <Seccion numero="11" titulo="Los demás que exija la ley" ayuda="Conciliación prejudicial u otro requisito de procedibilidad, poder, anexos, medidas cautelares, etc.">
              <textarea rows={3} value={form.otros_requisitos} onChange={set("otros_requisitos")} style={inputStyle} />
            </Seccion>
            <p style={{ fontSize: "12px", color: "#6b7f96" }}>
              Parágrafo 2: la demanda presentada como mensaje de datos no requiere firma digital; basta que el suscriptor se identifique con su nombre y documento.
            </p>

            <Campo label="Observaciones internas"><textarea rows={2} value={form.observaciones} onChange={set("observaciones")} style={inputStyle} /></Campo>
            <div style={{ display: "flex", gap: "10px", marginTop: "20px" }}>
              <button type="button" onClick={() => setForm(null)} style={{ ...botonSecundario, flex: 1 }}>Cancelar</button>
              <button type="submit" disabled={guardando} style={{ flex: 1, padding: "10px", borderRadius: "8px", border: "none", background: "#0a1a2b", color: "white", cursor: "pointer" }}>
                {guardando ? "Guardando..." : "Guardar"}
              </button>
            </div>
          </Modal>
        )}

        {detalle && (
          <Modal onClose={() => setDetalle(null)} ancho={640}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h2 style={{ margin: 0, fontSize: "18px" }}>{detalle.clase_proceso}</h2>
              <span onClick={() => setDetalle(null)} style={{ cursor: "pointer", fontSize: "22px" }}>&times;</span>
            </div>
            <p><Etiqueta texto={(ESTADOS[detalle.estado] || ESTADOS.elaboracion).label} bg={(ESTADOS[detalle.estado] || ESTADOS.elaboracion).bg} color={(ESTADOS[detalle.estado] || ESTADOS.elaboracion).color} /></p>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px", margin: "16px 0" }}>
              <Dato label="Demandante" value={detalle.demandante} />
              <Dato label="Demandado" value={detalle.demandado} />
              <Dato label="Cliente" value={detalle.cliente_nombre} />
              <Dato label="Juzgado" value={detalle.juzgado_nombre} />
              <Dato label="Cuantía" value={pesos(detalle.cuantia)} />
              <Dato label="Expediente" value={detalle.expediente_numero} />
              <Dato label="Radicación" value={fecha(detalle.fecha_radicacion)} />
              <Dato label="Responsable" value={detalle.abogado_nombre} />
              {detalle.estado === "inadmitida" && <Dato label="Auto de inadmisión" value={fecha(detalle.fecha_inadmision)} />}
              {detalle.estado === "inadmitida" && <Dato label="Subsanar hasta" value={textoSubsanacion(detalle)?.texto} />}
              {detalle.estado === "admitida" && <Dato label="Auto admisorio" value={fecha(detalle.fecha_admision)} />}
            </div>
            <Dato label="Pretensiones" value={<span style={{ whiteSpace: "pre-line" }}>{detalle.pretensiones}</span>} />
            {detalle.requisitos && (
              <div style={{ marginTop: "16px", border: "1px solid #e9edf2", borderRadius: "12px", padding: "12px 16px" }}>
                <div style={{ fontWeight: 700, marginBottom: "8px", display: "flex", gap: "10px", alignItems: "center" }}>
                  Requisitos del artículo 82 CGP <ChipRequisitos req={detalle.requisitos} />
                </div>
                {detalle.requisitos.items.map((x) => (
                  <div key={x.numeral} style={{ fontSize: "13px", padding: "3px 0" }}>
                    <span style={{ color: x.cumple === false ? "#c73a3a" : x.cumple ? "#1b8b5e" : "#6b7f96", fontWeight: 700 }}>
                      {x.cumple === false ? "✖" : x.cumple ? "✔" : "•"}
                    </span>{" "}
                    {x.numeral}. {x.titulo}
                    {x.falta.map((f, i) => <div key={i} style={{ marginLeft: "22px", color: "#c73a3a", fontSize: "12px" }}>{f}</div>)}
                  </div>
                ))}
                <div style={{ fontSize: "12px", color: "#6b7f96", marginTop: "6px" }}>El numeral 11 es informativo: depende de la clase de proceso.</div>
              </div>
            )}
            <Borrador key={detalle.id} ruta={`/demandas/${detalle.id}`} inicial={detalle.borrador} nombreArchivo={`demanda-${detalle.id}`} onGuardado={cargar} />
            {detalle.observaciones && <div style={{ marginTop: "14px" }}><Dato label="Observaciones" value={<span style={{ whiteSpace: "pre-line" }}>{detalle.observaciones}</span>} /></div>}
          </Modal>
        )}
      </div>
    </Layout>
  );
}
