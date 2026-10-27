import { useEffect, useState } from "react";
import { FileSignature } from "lucide-react";
import api from "../api";
import Layout from "../components/Layout";
import SelectorDespacho from "../components/SelectorDespacho";
import SelectorClaseProceso from "../components/SelectorClaseProceso";
import { Seccion, Casilla, ChipRequisitos, dosCol, TIPOS_PERSONA, TIPOS_DOC } from "../components/formulario";
import Borrador from "../components/Borrador";
import { mensajeError } from "../utils/errores";
import { fecha } from "../utils/formato";
import { Encabezado, Modal, Campo, Dato, Chip, Etiqueta, inputStyle, thStyle, tdStyle, botonSecundario, enlace, mensajeErrorEstilo } from "../components/ui";

const ESTADOS = {
  por_elaborar: { label: "Por elaborar", bg: "#e9ecf0", color: "#5b6f84" },
  en_elaboracion: { label: "En elaboración", bg: "#e3effa", color: "#2a6aa8" },
  presentada: { label: "Presentada", bg: "#e2f3e8", color: "#1b8b5e" },
  no_contestada: { label: "No contestada", bg: "#fde8e8", color: "#c73a3a" },
};

// Campos de los requisitos del artículo 96 del Código General del Proceso (con su valor inicial)
const HECHO_VACIO = { hecho: "", respuesta: "", razones: "" };
const EXCEPCION_VACIA = { nombre: "", fundamento: "" };
const ART96 = {
  demanda: "",
  demandado_tipo_persona: "natural", demandado_tipo_documento: "CC", demandado_documento: "", demandado_domicilio: "",
  demandado_representante: "", demandado_representante_documento: "",
  sin_apoderado: false, apoderado_nombre: "", apoderado_documento: "", apoderado_tarjeta_profesional: "", apoderado_domicilio: "",
  pronunciamiento_pretensiones: "", pronunciamientos_hechos: [{ ...HECHO_VACIO }],
  excepciones_merito: [{ ...EXCEPCION_VACIA }], sin_excepciones: false,
  objeta_juramento_estimatorio: false, objecion_juramento: "", alega_derecho_retencion: false, derecho_retencion: "",
  pruebas_en_expediente: false,
  notif_demandado_direccion: "", notif_demandado_email: "", notif_apoderado_direccion: "", notif_apoderado_email: "",
  anexo_poder: false, anexo_existencia_representacion: false, documentos_solicitados: "", anexos_otros: "",
};

const VACIO = {
  clase_proceso: "", demandante: "", demandado: "", cliente: "", expediente: "", juzgado: "", fecha_notificacion: "",
  dias_termino: 20, estado: "por_elaborar", fecha_presentacion: "", excepciones: "", pruebas: "", abogado_responsable: "", observaciones: "",
  ...ART96,
};
const NULABLES = ["cliente", "expediente", "juzgado", "demanda", "fecha_notificacion", "fecha_presentacion", "abogado_responsable"];
const RESPUESTAS = [["admite", "Se admite"], ["niega", "Se niega (no es cierto)"], ["no_consta", "No me consta"]];
const MIN_RAZONES = 10;

const hoyISO = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};

function textoLimite(c) {
  if (!c.fecha_limite) return null;
  const d = c.dias_restantes;
  if (d === null) return { texto: fecha(c.fecha_limite), color: "#6b7f96" };
  const cuando = d < 0 ? `vencido hace ${-d} d` : d === 0 ? "vence hoy" : `faltan ${d} d`;
  return { texto: `${fecha(c.fecha_limite)} (${cuando})`, color: d < 0 ? "#c73a3a" : d <= 3 ? "#a8681a" : "#1b8b5e" };
}

export default function Contestaciones() {
  const [lista, setLista] = useState([]);
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
  const [demandas, setDemandas] = useState([]);

  const cargar = () => {
    setCargando(true);
    api
      .get("/contestaciones/")
      .then((r) => setLista(r.data))
      .catch((err) => setError(mensajeError(err, "No se pudieron cargar las contestaciones.")))
      .finally(() => setCargando(false));
  };

  useEffect(() => {
    cargar();
    api.get("/clientes/").then((r) => setClientes(r.data)).catch(() => {});
    api.get("/juzgados/").then((r) => setJuzgados(r.data)).catch(() => {});
    api.get("/demandas/").then((r) => setDemandas(r.data)).catch(() => {});
    api.get("/expedientes/").then((r) => setExpedientes(r.data)).catch(() => {});
    api.get("/usuarios/").then((r) => setUsuarios(r.data)).catch(() => {});
    api.get("/perfil/").then((r) => setPerfil(r.data)).catch(() => {});
  }, []);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const abrirNueva = () => { setForm({ ...VACIO }); setEditandoId(null); setFormError(""); };
  const abrirEditar = (c) => {
    const art96 = Object.fromEntries(Object.entries(ART96).map(([k, v]) => [k, c[k] ?? v]));
    if (!art96.pronunciamientos_hechos.length) art96.pronunciamientos_hechos = [{ ...HECHO_VACIO }];
    if (!art96.excepciones_merito.length) art96.excepciones_merito = [{ ...EXCEPCION_VACIA }];
    art96.demanda = c.demanda || "";
    setForm({
      clase_proceso: c.clase_proceso, demandante: c.demandante, demandado: c.demandado, cliente: c.cliente || "",
      expediente: c.expediente || "", juzgado: c.juzgado || "", fecha_notificacion: c.fecha_notificacion || "",
      dias_termino: c.dias_termino, estado: c.estado, fecha_presentacion: c.fecha_presentacion || "",
      excepciones: c.excepciones || "", pruebas: c.pruebas || "", abogado_responsable: c.abogado_responsable || "",
      observaciones: c.observaciones || "",
      ...art96,
    });
    setEditandoId(c.id);
    setFormError("");
  };

  const setCheck = (k) => (e) => setForm({ ...form, [k]: e.target.checked });
  const cambiarTipoPersona = (e) => setForm({
    ...form,
    demandado_tipo_persona: e.target.value,
    demandado_tipo_documento: e.target.value === "juridica" ? "NIT" : form.demandado_tipo_documento === "NIT" ? "CC" : form.demandado_tipo_documento,
  });
  const setHecho = (i, campo, v) => setForm({ ...form, pronunciamientos_hechos: form.pronunciamientos_hechos.map((h, j) => (j === i ? { ...h, [campo]: v } : h)) });
  const agregarHecho = () => setForm({ ...form, pronunciamientos_hechos: [...form.pronunciamientos_hechos, { ...HECHO_VACIO }] });
  const quitarHecho = (i) => {
    const resto = form.pronunciamientos_hechos.filter((_, j) => j !== i);
    setForm({ ...form, pronunciamientos_hechos: resto.length ? resto : [{ ...HECHO_VACIO }] });
  };
  const setExcepcion = (i, campo, v) => setForm({ ...form, excepciones_merito: form.excepciones_merito.map((x, j) => (j === i ? { ...x, [campo]: v } : x)) });
  const agregarExcepcion = () => setForm({ ...form, excepciones_merito: [...form.excepciones_merito, { ...EXCEPCION_VACIA }] });
  const quitarExcepcion = (i) => {
    const resto = form.excepciones_merito.filter((_, j) => j !== i);
    setForm({ ...form, excepciones_merito: resto.length ? resto : [{ ...EXCEPCION_VACIA }] });
  };

  const demandaElegida = demandas.find((d) => String(d.id) === String(form?.demanda));
  const hechosDeLaDemanda = (d) => (d.hechos || []).map((h) => ({ hecho: h, respuesta: "", razones: "" }));
  const hayHechosEscritos = (f) => f.pronunciamientos_hechos.some((h) => h.hecho.trim() || h.razones.trim());

  // Al elegir la demanda se completan los campos que estén vacíos con lo que ya se sabe de ella.
  const elegirDemanda = (id) => {
    const d = demandas.find((x) => String(x.id) === String(id));
    if (!d) return setForm({ ...form, demanda: "" });
    const vacio = (v) => v === "" || v === null || v === undefined;
    const nuevo = { ...form, demanda: d.id };
    const copiar = (k, valor) => { if (vacio(nuevo[k]) && !vacio(valor)) nuevo[k] = valor; };
    copiar("clase_proceso", d.clase_proceso);
    copiar("demandante", d.demandante);
    copiar("demandado", d.demandado);
    copiar("cliente", d.cliente);
    copiar("expediente", d.expediente);
    copiar("juzgado", d.juzgado);
    if (!form.demandado_documento && !form.demandado_domicilio) {
      nuevo.demandado_tipo_persona = d.demandado_tipo_persona || nuevo.demandado_tipo_persona;
      nuevo.demandado_tipo_documento = d.demandado_tipo_documento || nuevo.demandado_tipo_documento;
      copiar("demandado_documento", d.demandado_documento);
      copiar("demandado_domicilio", d.demandado_domicilio);
      copiar("demandado_representante", d.demandado_representante);
    }
    copiar("notif_demandado_direccion", d.notif_demandado_direccion);
    copiar("notif_demandado_email", d.notif_demandado_email);
    if (!hayHechosEscritos(form) && (d.hechos || []).length) nuevo.pronunciamientos_hechos = hechosDeLaDemanda(d);
    setForm(nuevo);
  };

  const traerHechos = () => {
    if (!demandaElegida || !(demandaElegida.hechos || []).length) return alert("La demanda seleccionada no tiene hechos registrados.");
    if (hayHechosEscritos(form) && !window.confirm("Se reemplazará el pronunciamiento actual por los hechos de la demanda. ¿Continuar?")) return;
    setForm({ ...form, pronunciamientos_hechos: hechosDeLaDemanda(demandaElegida) });
  };

  const guardar = async (e) => {
    e.preventDefault();
    setFormError("");
    const dias = Number(form.dias_termino);
    if (!Number.isInteger(dias) || dias < 1 || dias > 90) return setFormError("El término debe estar entre 1 y 90 días hábiles.");
    setGuardando(true);
    try {
      const datos = { ...form, dias_termino: dias };
      NULABLES.forEach((k) => { if (datos[k] === "") { if (editandoId) datos[k] = null; else delete datos[k]; } });
      datos.pronunciamientos_hechos = datos.pronunciamientos_hechos.filter((h) => h.hecho.trim() || h.razones.trim() || h.respuesta);
      datos.excepciones_merito = datos.excepciones_merito.filter((x) => x.nombre.trim() || x.fundamento.trim());
      const r = editandoId ? await api.patch(`/contestaciones/${editandoId}/`, datos) : await api.post("/contestaciones/", datos);
      setForm(null);
      setEditandoId(null);
      cargar();
      // Si ya se marcó como presentada, se avisa qué numerales del art. 96 faltan
      const req = r.data.requisitos;
      if (r.data.estado === "presentada" && req && req.cumplidos < req.total) {
        const faltas = req.items.filter((x) => x.cumple === false).map((x) => (x.numeral === 6 ? "Anexos" : `${x.numeral}. ${x.titulo}`)).join("\n");
        alert(`La contestación se guardó, pero aún no cumple todos los requisitos del artículo 96 del CGP (${req.cumplidos}/${req.total}). Falta:\n\n${faltas}`);
      }
    } catch (err) {
      setFormError(mensajeError(err, "No se pudo guardar la contestación."));
    } finally {
      setGuardando(false);
    }
  };

  const eliminar = async (c) => {
    if (!window.confirm("¿Eliminar esta contestación? Esta acción no se puede deshacer.")) return;
    try {
      await api.delete(`/contestaciones/${c.id}/`);
      cargar();
    } catch (err) {
      alert(mensajeError(err, "No se pudo eliminar."));
    }
  };

  const conteo = (est) => lista.filter((c) => c.estado === est).length;
  const urgentes = lista.filter((c) => c.dias_restantes !== null && c.dias_restantes <= 3).length;
  const visibles = lista.filter((c) => {
    const t = busqueda.toLowerCase();
    const coincide = [c.demandante, c.demandado, c.clase_proceso, c.cliente_nombre || ""].some((x) => x.toLowerCase().includes(t));
    return coincide && (!filtro || c.estado === filtro);
  });

  return (
    <Layout>
      <div style={{ minHeight: "100vh", background: "#f4f7fb", fontFamily: "sans-serif" }}>
        <Encabezado Icono={FileSignature} titulo="B1 · Contestación de demanda" busqueda={busqueda} setBusqueda={setBusqueda} placeholder="Buscar contestación..." textoBoton="+ Nueva contestación" onNuevo={abrirNueva} />
        <main style={{ padding: "32px" }}>
          <p style={{ color: "#6b7f96", fontSize: "13px", marginTop: 0 }}>
            El plazo se cuenta en días hábiles desde la notificación (20 días por defecto en el proceso verbal; puede cambiarlo según la clase de proceso).
            Los festivos de Colombia se descuentan automáticamente; no se descuenta la vacancia judicial.
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
              {urgentes > 0 && (
                <p style={{ background: "#fff3d6", color: "#a8681a", padding: "10px 14px", borderRadius: "10px", fontSize: "14px" }}>
                  ⚠ {urgentes} contestación(es) con el término vencido o por vencer en 3 días hábiles o menos.
                </p>
              )}
              <div style={{ background: "white", borderRadius: "16px", border: "1px solid #eef2f6", overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
                  <thead>
                    <tr style={{ background: "#f8fafc" }}>
                      {["Proceso", "Partes", "Notificación", "Vence", "Estado", "Art. 96", "Responsable", "Acción"].map((h) => <th key={h} style={thStyle}>{h}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {visibles.map((c) => {
                      const est = ESTADOS[c.estado] || ESTADOS.por_elaborar;
                      const lim = textoLimite(c);
                      return (
                        <tr key={c.id} style={{ borderTop: "1px solid #f0f3f8" }}>
                          <td style={tdStyle}>
                            <strong>{c.clase_proceso}</strong>
                            <div style={{ color: "#6b7f96", fontSize: "12px" }}>{c.expediente_numero || "Sin expediente"}</div>
                          </td>
                          <td style={tdStyle}>{c.demandante} <span style={{ color: "#6b7f96" }}>vs</span> {c.demandado}</td>
                          <td style={tdStyle}>{fecha(c.fecha_notificacion)}</td>
                          <td style={tdStyle}>
                            {lim ? <span style={{ color: lim.color, fontWeight: 600 }}>{lim.texto}</span> : "—"}
                            {c.extemporanea && <div style={{ color: "#c73a3a", fontSize: "12px", fontWeight: 600 }}>Presentada fuera de término</div>}
                          </td>
                          <td style={tdStyle}><Etiqueta texto={est.label} bg={est.bg} color={est.color} /></td>
                          <td style={tdStyle}><ChipRequisitos req={c.requisitos} /></td>
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
                  <p style={{ padding: "24px", color: "#6b7f96" }}>{lista.length === 0 ? "Aún no hay contestaciones registradas." : "No hay contestaciones que coincidan."}</p>
                )}
              </div>
            </>
          )}
        </main>

        {form && (
          <Modal onClose={() => setForm(null)} comoFormulario onSubmit={guardar} ancho={860}>
            <h2 style={{ marginTop: 0 }}>{editandoId ? "✏️ Editar contestación" : "+ Nueva contestación"}</h2>
            <p style={{ fontSize: "13px", color: "#6b7f96", marginTop: 0 }}>
              El formulario sigue los requisitos del artículo 96 del Código General del Proceso. Puede guardar la contestación incompleta y terminarla después;
              el sistema le indica qué numerales faltan.
            </p>
            {formError && <p style={mensajeErrorEstilo}>{formError}</p>}

            <Seccion titulo="Datos generales">
              <Campo label="Demanda que se contesta (A1)" ayuda="Opcional. Al elegirla se completan los datos que ya se conocen y se traen los hechos de la demanda.">
                <select value={form.demanda} onChange={(e) => elegirDemanda(e.target.value)} style={inputStyle}>
                  <option value="">Sin vincular</option>
                  {demandas.map((d) => <option key={d.id} value={d.id}>{d.clase_proceso}: {d.demandante} vs {d.demandado}</option>)}
                </select>
              </Campo>
              <Campo label="Clase de proceso">
                <SelectorClaseProceso value={form.clase_proceso} onChange={(v) => setForm({ ...form, clase_proceso: v })} required />
              </Campo>
              <div style={dosCol}>
                <Campo label="Fecha de notificación del demandado" ayuda="Con ella se calcula el vencimiento.">
                  <input type="date" max={hoyISO()} value={form.fecha_notificacion} onChange={set("fecha_notificacion")} style={inputStyle} />
                </Campo>
                <Campo label="Término (días hábiles)"><input type="number" min="1" max="90" value={form.dias_termino} onChange={set("dias_termino")} style={inputStyle} /></Campo>
                <Campo label="Estado">
                  <select value={form.estado} onChange={set("estado")} style={inputStyle}>
                    {Object.entries(ESTADOS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
                  </select>
                </Campo>
                {form.estado === "presentada" && (
                  <Campo label="Fecha de presentación"><input type="date" max={hoyISO()} value={form.fecha_presentacion} onChange={set("fecha_presentacion")} style={inputStyle} /></Campo>
                )}
                <Campo label="Cliente">
                  <select value={form.cliente} onChange={set("cliente")} style={inputStyle}>
                    <option value="">Sin cliente</option>
                    {clientes.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
                  </select>
                </Campo>
                <Campo label="Expediente">
                  <select value={form.expediente} onChange={set("expediente")} style={inputStyle}>
                    <option value="">Sin expediente</option>
                    {expedientes.map((x) => <option key={x.id} value={x.id}>{x.numero} · {x.demandante}</option>)}
                  </select>
                </Campo>
                <div style={{ gridColumn: "1 / -1" }}>
                  <SelectorDespacho juzgados={juzgados} value={form.juzgado} onChange={(v) => setForm({ ...form, juzgado: v })} />
                </div>
              </div>
              {perfil?.es_directivo && (
                <Campo label="Abogado responsable en el sistema">
                  <select value={form.abogado_responsable} onChange={set("abogado_responsable")} style={inputStyle}>
                    <option value="">Yo (por defecto)</option>
                    {usuarios.map((u) => <option key={u.id} value={u.id}>{u.nombre_completo}</option>)}
                  </select>
                </Campo>
              )}
            </Seccion>

            <Seccion numero="1" titulo="El demandado y su representante o apoderado" ayuda="Nombre, domicilio y número de documento de identificación. Las personas jurídicas y los patrimonios autónomos se identifican con NIT.">
              <div style={dosCol}>
                <Campo label="Demandante (quien presentó la demanda)"><input value={form.demandante} onChange={set("demandante")} required style={inputStyle} /></Campo>
                <Campo label="Demandado (quien contesta)"><input value={form.demandado} onChange={set("demandado")} required style={inputStyle} /></Campo>
                <Campo label="Tipo de persona">
                  <select value={form.demandado_tipo_persona} onChange={cambiarTipoPersona} style={inputStyle}>
                    {TIPOS_PERSONA.map(([v, t]) => <option key={v} value={v}>{t}</option>)}
                  </select>
                </Campo>
                <div style={dosCol}>
                  <Campo label="Tipo de documento">
                    <select value={form.demandado_tipo_documento} onChange={set("demandado_tipo_documento")} disabled={form.demandado_tipo_persona === "juridica"} style={inputStyle}>
                      <option value="">Seleccione</option>
                      {TIPOS_DOC.map(([v, t]) => <option key={v} value={v}>{t}</option>)}
                    </select>
                  </Campo>
                  <Campo label="Número"><input value={form.demandado_documento} onChange={set("demandado_documento")} placeholder={form.demandado_tipo_persona === "juridica" ? "900123456-7" : "Sin puntos"} style={inputStyle} /></Campo>
                </div>
                <Campo label="Domicilio del demandado"><input value={form.demandado_domicilio} onChange={set("demandado_domicilio")} placeholder="Ciudad y departamento" style={inputStyle} /></Campo>
                <div />
                <Campo label="Representante legal (si aplica)"><input value={form.demandado_representante} onChange={set("demandado_representante")} style={inputStyle} /></Campo>
                <Campo label="Documento del representante"><input value={form.demandado_representante_documento} onChange={set("demandado_representante_documento")} placeholder="Ej.: C.C. 12345678" style={inputStyle} /></Campo>
              </div>
              <Casilla checked={form.sin_apoderado} onChange={setCheck("sin_apoderado")}>El demandado comparece por sí mismo, sin apoderado</Casilla>
              {!form.sin_apoderado && (
                <div style={dosCol}>
                  <Campo label="Nombre del apoderado"><input value={form.apoderado_nombre} onChange={set("apoderado_nombre")} style={inputStyle} /></Campo>
                  <Campo label="Cédula (C.C.)"><input value={form.apoderado_documento} onChange={set("apoderado_documento")} style={inputStyle} /></Campo>
                  <Campo label="Tarjeta profesional (T.P.)"><input value={form.apoderado_tarjeta_profesional} onChange={set("apoderado_tarjeta_profesional")} style={inputStyle} /></Campo>
                  <Campo label="Domicilio del apoderado"><input value={form.apoderado_domicilio} onChange={set("apoderado_domicilio")} style={inputStyle} /></Campo>
                </div>
              )}
            </Seccion>

            <Seccion numero="2" titulo="Pronunciamiento sobre las pretensiones y los hechos" ayuda="Debe ser expreso y concreto. Indique los hechos que admite, los que niega y los que no le constan; en los dos últimos casos explique las razones de forma precisa y unívoca. Si no lo hace, se presumirá cierto el hecho.">
              {demandaElegida && (
                <div style={{ background: "#f4f7fb", borderRadius: "10px", padding: "10px 12px", fontSize: "13px", marginBottom: "12px" }}>
                  <strong>Pretensiones de la demanda:</strong>
                  <div style={{ whiteSpace: "pre-line", color: "#3d5167" }}>{demandaElegida.pretensiones}</div>
                </div>
              )}
              <Campo label="Pronunciamiento sobre las pretensiones">
                <textarea rows={3} value={form.pronunciamiento_pretensiones} onChange={set("pronunciamiento_pretensiones")} placeholder="Ej.: Me opongo a todas las pretensiones, por las razones expuestas en las excepciones." style={inputStyle} />
              </Campo>
              <div style={{ fontWeight: 600, margin: "6px 0 8px" }}>Hechos de la demanda</div>
              {form.pronunciamientos_hechos.map((h, i) => {
                const requiereRazones = h.respuesta === "niega" || h.respuesta === "no_consta";
                const faltaRazon = requiereRazones && h.razones.trim().length < MIN_RAZONES;
                return (
                  <div key={i} style={{ border: "1px solid #e9edf2", borderRadius: "10px", padding: "10px", marginBottom: "10px", background: "white" }}>
                    <div style={{ display: "grid", gridTemplateColumns: "28px 1fr 24px", gap: "8px", alignItems: "start" }}>
                      <strong style={{ paddingTop: "8px" }}>{i + 1}.</strong>
                      <textarea rows={2} value={h.hecho} onChange={(e) => setHecho(i, "hecho", e.target.value)} placeholder="Hecho de la demanda (transcríbalo o resúmalo)" style={inputStyle} />
                      <button type="button" onClick={() => quitarHecho(i)} title="Quitar" style={{ border: "none", background: "none", color: "#c73a3a", cursor: "pointer", paddingTop: "6px" }}>✕</button>
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "220px 1fr", gap: "10px", marginTop: "8px", paddingLeft: "36px" }}>
                      <select value={h.respuesta} onChange={(e) => setHecho(i, "respuesta", e.target.value)} style={inputStyle}>
                        <option value="">¿Qué responde?</option>
                        {RESPUESTAS.map(([v, t]) => <option key={v} value={v}>{t}</option>)}
                      </select>
                      <textarea
                        rows={2}
                        value={h.razones}
                        onChange={(e) => setHecho(i, "razones", e.target.value)}
                        placeholder={requiereRazones ? "Razones de la respuesta (obligatorio)" : "Razones (opcional)"}
                        style={{ ...inputStyle, borderColor: faltaRazon ? "#c73a3a" : "#d0d9e3" }}
                      />
                    </div>
                    {faltaRazon && (
                      <div style={{ paddingLeft: "36px", marginTop: "4px", fontSize: "12px", color: "#c73a3a" }}>
                        Explique las razones de forma precisa y unívoca; de lo contrario este hecho se presumirá cierto.
                      </div>
                    )}
                  </div>
                );
              })}
              <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                <button type="button" onClick={agregarHecho} style={botonSecundario}>+ Agregar hecho</button>
                {demandaElegida && <button type="button" onClick={traerHechos} style={botonSecundario}>Traer los hechos de la demanda</button>}
              </div>
            </Seccion>

            <Seccion numero="3" titulo="Excepciones de mérito, juramento estimatorio y derecho de retención" ayuda="Cada excepción de mérito con el fundamento fáctico que la sustenta.">
              <Casilla checked={form.sin_excepciones} onChange={setCheck("sin_excepciones")}>No se propone ninguna excepción de mérito</Casilla>
              {!form.sin_excepciones && (
                <>
                  {form.excepciones_merito.map((x, i) => (
                    <div key={i} style={{ border: "1px solid #e9edf2", borderRadius: "10px", padding: "10px", marginBottom: "10px", background: "white" }}>
                      <div style={{ display: "grid", gridTemplateColumns: "28px 1fr 24px", gap: "8px", alignItems: "start" }}>
                        <strong style={{ paddingTop: "8px" }}>{i + 1}.</strong>
                        <input value={x.nombre} onChange={(e) => setExcepcion(i, "nombre", e.target.value)} placeholder="Nombre de la excepción (p. ej. Prescripción de la acción cambiaria)" style={inputStyle} />
                        <button type="button" onClick={() => quitarExcepcion(i)} title="Quitar" style={{ border: "none", background: "none", color: "#c73a3a", cursor: "pointer", paddingTop: "6px" }}>✕</button>
                      </div>
                      <div style={{ paddingLeft: "36px", marginTop: "8px" }}>
                        <textarea rows={3} value={x.fundamento} onChange={(e) => setExcepcion(i, "fundamento", e.target.value)} placeholder="Fundamento fáctico de la excepción" style={inputStyle} />
                      </div>
                    </div>
                  ))}
                  <button type="button" onClick={agregarExcepcion} style={{ ...botonSecundario, marginBottom: "12px" }}>+ Agregar excepción</button>
                </>
              )}
              <Campo label="Excepciones previas y otras consideraciones (opcional)">
                <textarea rows={2} value={form.excepciones} onChange={set("excepciones")} style={inputStyle} />
              </Campo>
              <Casilla checked={form.objeta_juramento_estimatorio} onChange={setCheck("objeta_juramento_estimatorio")}>Se objeta el juramento estimatorio de la demanda</Casilla>
              {form.objeta_juramento_estimatorio && (
                <textarea rows={3} value={form.objecion_juramento} onChange={set("objecion_juramento")} placeholder="Objeción razonada, especificando la inexactitud que se le atribuye a la estimación" style={{ ...inputStyle, marginBottom: "12px" }} />
              )}
              <Casilla checked={form.alega_derecho_retencion} onChange={setCheck("alega_derecho_retencion")}>Se alega el derecho de retención</Casilla>
              {form.alega_derecho_retencion && (
                <textarea rows={3} value={form.derecho_retencion} onChange={set("derecho_retencion")} placeholder="Bien sobre el que se ejerce la retención y su fundamento" style={inputStyle} />
              )}
            </Seccion>

            <Seccion numero="4" titulo="Petición de pruebas" ayuda="Las que el demandado pretenda hacer valer, si no obran en el expediente.">
              <Campo label="Pruebas que se solicitan o aportan"><textarea rows={3} value={form.pruebas} onChange={set("pruebas")} style={inputStyle} /></Campo>
              <Casilla checked={form.pruebas_en_expediente} onChange={setCheck("pruebas_en_expediente")}>Las pruebas que se quieren hacer valer ya obran en el expediente</Casilla>
            </Seccion>

            <Seccion numero="5" titulo="Lugar y direcciones para notificaciones" ayuda="Dirección física y de correo electrónico donde el demandado, su representante o su apoderado recibirán notificaciones personales.">
              <div style={dosCol}>
                <Campo label="Demandado: dirección física"><input value={form.notif_demandado_direccion} onChange={set("notif_demandado_direccion")} style={inputStyle} /></Campo>
                <Campo label="Demandado: correo electrónico"><input type="email" value={form.notif_demandado_email} onChange={set("notif_demandado_email")} style={inputStyle} /></Campo>
                {!form.sin_apoderado && (
                  <>
                    <Campo label="Apoderado: dirección física"><input value={form.notif_apoderado_direccion} onChange={set("notif_apoderado_direccion")} style={inputStyle} /></Campo>
                    <Campo label="Apoderado: correo electrónico"><input type="email" value={form.notif_apoderado_email} onChange={set("notif_apoderado_email")} style={inputStyle} /></Campo>
                  </>
                )}
              </div>
            </Seccion>

            <Seccion titulo="Anexos de la contestación" ayuda="A la contestación debe acompañarse el poder, la prueba de existencia y representación (si hay lugar), los documentos en su poder que haya solicitado el demandante (o la manifestación de que no los tiene) y las pruebas que pretenda hacer valer.">
              {!form.sin_apoderado && <Casilla checked={form.anexo_poder} onChange={setCheck("anexo_poder")}>Se anexa el poder de quien suscribe la contestación</Casilla>}
              {form.demandado_tipo_persona === "juridica" && (
                <Casilla checked={form.anexo_existencia_representacion} onChange={setCheck("anexo_existencia_representacion")}>Se anexa la prueba de existencia y representación del demandado</Casilla>
              )}
              <Campo label="Documentos en su poder solicitados por el demandante (o manifestación de que no los tiene)">
                <textarea rows={2} value={form.documentos_solicitados} onChange={set("documentos_solicitados")} style={inputStyle} />
              </Campo>
              <Campo label="Otros anexos"><textarea rows={2} value={form.anexos_otros} onChange={set("anexos_otros")} style={inputStyle} /></Campo>
            </Seccion>

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
              <h2 style={{ margin: 0, fontSize: "18px" }}>Contestación · {detalle.clase_proceso}</h2>
              <span onClick={() => setDetalle(null)} style={{ cursor: "pointer", fontSize: "22px" }}>&times;</span>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px", margin: "16px 0" }}>
              <Dato label="Demandante" value={detalle.demandante} />
              <Dato label="Demandado" value={detalle.demandado} />
              <Dato label="Cliente" value={detalle.cliente_nombre} />
              <Dato label="Juzgado" value={detalle.juzgado_nombre} />
              <Dato label="Notificación" value={fecha(detalle.fecha_notificacion)} />
              <Dato label={`Vence (${detalle.dias_termino} días hábiles)`} value={textoLimite(detalle)?.texto} />
              <Dato label="Expediente" value={detalle.expediente_numero} />
              <Dato label="Responsable" value={detalle.abogado_nombre} />
              {detalle.estado === "presentada" && <Dato label="Presentada el" value={fecha(detalle.fecha_presentacion)} />}
            </div>
            {detalle.extemporanea && <p style={{ color: "#c73a3a", fontWeight: 600 }}>La contestación se presentó después del vencimiento del término.</p>}
            {detalle.demanda_texto && <div style={{ marginBottom: "12px" }}><Dato label="Demanda que se contesta" value={detalle.demanda_texto} /></div>}
            {(detalle.excepciones_merito || []).length > 0 && (
              <Dato label="Excepciones de mérito" value={detalle.excepciones_merito.map((x) => x.nombre).join(" · ")} />
            )}
            {detalle.pruebas && <div style={{ marginTop: "12px" }}><Dato label="Pruebas" value={<span style={{ whiteSpace: "pre-line" }}>{detalle.pruebas}</span>} /></div>}
            {detalle.requisitos && (
              <div style={{ marginTop: "16px", border: "1px solid #e9edf2", borderRadius: "12px", padding: "12px 16px" }}>
                <div style={{ fontWeight: 700, marginBottom: "8px", display: "flex", gap: "10px", alignItems: "center" }}>
                  Requisitos del artículo 96 CGP <ChipRequisitos req={detalle.requisitos} />
                </div>
                {detalle.requisitos.items.map((x) => (
                  <div key={x.numeral} style={{ fontSize: "13px", padding: "3px 0" }}>
                    <span style={{ color: x.cumple ? "#1b8b5e" : "#c73a3a", fontWeight: 700 }}>{x.cumple ? "✔" : "✖"}</span>{" "}
                    {x.numeral === 6 ? "Anexos" : `${x.numeral}.`} {x.titulo}
                    {x.falta.map((f, i) => <div key={i} style={{ marginLeft: "22px", color: "#c73a3a", fontSize: "12px" }}>{f}</div>)}
                  </div>
                ))}
                <div style={{ fontSize: "12px", color: "#6b7f96", marginTop: "6px" }}>
                  Recuerde: los hechos que se nieguen o que no le consten deben explicarse de forma precisa y unívoca; si no, se presumen ciertos.
                </div>
              </div>
            )}
            <Borrador key={detalle.id} ruta={`/contestaciones/${detalle.id}`} inicial={detalle.borrador} nombreArchivo={`contestacion-${detalle.id}`} onGuardado={cargar} />
          </Modal>
        )}
      </div>
    </Layout>
  );
}
