import { useEffect, useState } from "react";
import { Home } from "lucide-react";
import api from "../api";
import Layout from "../components/Layout";
import { mensajeError } from "../utils/errores";
import { fecha, pesos } from "../utils/formato";
import { Encabezado, Dato, Etiqueta, inputStyle, botonPrimario, enlace, mensajeErrorEstilo } from "../components/ui";

const tarjeta = { background: "white", borderRadius: "16px", border: "1px solid #eef2f6", padding: "20px", marginBottom: "20px" };
const ETAPA = {
  pendiente: { texto: "Pendiente", bg: "#fff3d6", color: "#a8681a" },
  en_curso: { texto: "En curso", bg: "#e3effa", color: "#2a6aa8" },
  completada: { texto: "Completada", bg: "#e2f3e8", color: "#1b8b5e" },
};

export default function Portal() {
  const [procesos, setProcesos] = useState([]);
  const [facturas, setFacturas] = useState([]);
  const [seleccionado, setSeleccionado] = useState(null);
  const [documentos, setDocumentos] = useState([]);
  const [mensajes, setMensajes] = useState([]);
  const [texto, setTexto] = useState("");
  const [error, setError] = useState("");
  const [errorAccion, setErrorAccion] = useState("");
  const [cargando, setCargando] = useState(true);
  const [subiendo, setSubiendo] = useState(false);

  useEffect(() => {
    api
      .get("/portal/expedientes/")
      .then((r) => {
        setProcesos(r.data);
        if (r.data.length) setSeleccionado(r.data[0].id);
      })
      .catch((err) => setError(mensajeError(err, "No se pudo cargar su información.")))
      .finally(() => setCargando(false));
    api.get("/portal/facturas/").then((r) => setFacturas(r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (!seleccionado) return;
    setDocumentos([]);
    setMensajes([]);
    setErrorAccion("");
    api.get(`/portal/expedientes/${seleccionado}/documentos/`).then((r) => setDocumentos(r.data)).catch(() => {});
    api.get(`/portal/expedientes/${seleccionado}/mensajes/`).then((r) => setMensajes(r.data)).catch(() => {});
  }, [seleccionado]);

  const proceso = procesos.find((p) => p.id === seleccionado) || null;

  const descargar = async (d) => {
    try {
      const r = await api.get(`/portal/expedientes/${seleccionado}/documentos/${d.id}/`, { responseType: "blob" });
      const url = URL.createObjectURL(r.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = d.nombre;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setErrorAccion(mensajeError(err, "No se pudo descargar el documento."));
    }
  };

  const subir = async (e) => {
    const archivo = e.target.files?.[0];
    e.target.value = "";
    if (!archivo) return;
    setErrorAccion("");
    setSubiendo(true);
    const datos = new FormData();
    datos.append("archivo", archivo);
    try {
      const r = await api.post(`/portal/expedientes/${seleccionado}/documentos/`, datos);
      setDocumentos((prev) => [r.data, ...prev]);
    } catch (err) {
      setErrorAccion(mensajeError(err, "No se pudo subir el documento."));
    } finally {
      setSubiendo(false);
    }
  };

  const enviar = async (e) => {
    e.preventDefault();
    setErrorAccion("");
    try {
      const r = await api.post(`/portal/expedientes/${seleccionado}/mensajes/`, { texto });
      setMensajes((prev) => [...prev, r.data]);
      setTexto("");
    } catch (err) {
      setErrorAccion(mensajeError(err, "No se pudo enviar el mensaje."));
    }
  };

  return (
    <Layout>
      <div style={{ minHeight: "100vh", background: "#f4f7fb", fontFamily: "sans-serif" }}>
        <Encabezado Icono={Home} titulo="Mi portal" />
        <main style={{ padding: "32px", maxWidth: "960px" }}>
          {cargando && <p>Cargando...</p>}
          {error && <p style={mensajeErrorEstilo}>{error}</p>}
          {!cargando && !error && procesos.length === 0 && (
            <p style={{ color: "#6b7f96" }}>Por ahora no tiene procesos registrados con el despacho.</p>
          )}

          {procesos.length > 1 && (
            <select value={seleccionado || ""} onChange={(e) => setSeleccionado(Number(e.target.value))} style={{ ...inputStyle, maxWidth: "420px", marginBottom: "16px" }}>
              {procesos.map((p) => <option key={p.id} value={p.id}>{p.numero} · {p.materia}</option>)}
            </select>
          )}

          {proceso && (
            <>
              <section style={tarjeta}>
                <h3 style={{ marginTop: 0 }}>Proceso {proceso.numero}</h3>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px" }}>
                  <Dato label="Estado" value={proceso.estado_display} />
                  <Dato label="Materia" value={proceso.materia} />
                  <Dato label="Juzgado" value={proceso.juzgado_nombre} />
                  <Dato label="Su abogado" value={proceso.abogado_nombre} />
                  <Dato label="Demandante" value={proceso.demandante} />
                  <Dato label="Demandado" value={proceso.demandado} />
                </div>
              </section>

              <section style={tarjeta}>
                <h3 style={{ marginTop: 0 }}>Avance y próximas fechas</h3>
                {proceso.etapas.length === 0 && proceso.audiencias.length === 0 && <p style={{ color: "#6b7f96", fontSize: "14px" }}>Aún no hay etapas ni audiencias registradas.</p>}
                {proceso.etapas.map((et) => {
                  const e = ETAPA[et.estado] || ETAPA.pendiente;
                  return (
                    <div key={et.id} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px dashed #e9edf2", fontSize: "14px" }}>
                      <span>{et.nombre}{et.fecha_limite ? ` · ${fecha(et.fecha_limite)}` : ""}</span>
                      <Etiqueta texto={e.texto} bg={e.bg} color={e.color} />
                    </div>
                  );
                })}
                {proceso.audiencias.map((a) => (
                  <div key={a.id} style={{ padding: "6px 0", borderBottom: "1px dashed #e9edf2", fontSize: "14px" }}>
                    📅 <strong>{a.tipo_display}{a.clase ? ` · ${a.clase}` : ""}</strong> · {new Date(a.fecha_hora).toLocaleString("es-CO")} · {a.lugar}
                  </div>
                ))}
              </section>

              <section style={tarjeta}>
                <h3 style={{ marginTop: 0 }}>Documentos</h3>
                {errorAccion && <p style={mensajeErrorEstilo}>{errorAccion}</p>}
                {documentos.length === 0 && <p style={{ color: "#6b7f96", fontSize: "14px" }}>El despacho aún no ha compartido documentos.</p>}
                {documentos.map((d) => (
                  <div key={d.id} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px dashed #e9edf2", fontSize: "14px" }}>
                    <span>{d.nombre} {d.origen_cliente && <span style={{ color: "#6b7f96", fontSize: "12px" }}>(enviado por usted)</span>}</span>
                    <button style={enlace()} onClick={() => descargar(d)}>Descargar</button>
                  </div>
                ))}
                <label style={{ ...botonPrimario, display: "inline-block", marginTop: "12px", opacity: subiendo ? 0.6 : 1 }}>
                  {subiendo ? "Subiendo..." : "+ Enviar un documento al despacho"}
                  <input type="file" onChange={subir} disabled={subiendo} style={{ display: "none" }} accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.txt" />
                </label>
                <p style={{ fontSize: "11px", color: "#6b7f96" }}>PDF, Word, Excel, imágenes o texto. Máximo 5 MB.</p>
              </section>

              <section style={tarjeta}>
                <h3 style={{ marginTop: 0 }}>Mensajes con el despacho</h3>
                {mensajes.length === 0 && <p style={{ color: "#6b7f96", fontSize: "14px" }}>Aún no hay mensajes.</p>}
                {mensajes.map((m) => (
                  <div key={m.id} style={{ padding: "8px 12px", margin: "6px 0", borderRadius: "10px", fontSize: "14px", background: m.de_cliente ? "#e3effa" : "#f0f3f8" }}>
                    <strong>{m.de_cliente ? "Usted" : m.autor_nombre}</strong> · <span style={{ color: "#6b7f96" }}>{new Date(m.creado_en).toLocaleString("es-CO")}</span>
                    <div style={{ whiteSpace: "pre-line" }}>{m.texto}</div>
                  </div>
                ))}
                <form onSubmit={enviar} style={{ display: "flex", gap: "8px", marginTop: "10px" }}>
                  <input value={texto} onChange={(e) => setTexto(e.target.value)} placeholder="Escriba su mensaje..." maxLength={2000} style={{ ...inputStyle, flex: 1 }} />
                  <button type="submit" disabled={!texto.trim()} style={botonPrimario}>Enviar</button>
                </form>
              </section>
            </>
          )}

          {facturas.length > 0 && (
            <section style={tarjeta}>
              <h3 style={{ marginTop: 0 }}>Mis facturas</h3>
              {facturas.map((f) => (
                <div key={f.id} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px dashed #e9edf2", fontSize: "14px" }}>
                  <span>{f.numero} · {f.concepto}{f.fecha_vencimiento ? ` · vence ${fecha(f.fecha_vencimiento)}` : ""}</span>
                  <span><strong>{pesos(f.monto)}</strong> · {f.estado_display}</span>
                </div>
              ))}
            </section>
          )}
        </main>
      </div>
    </Layout>
  );
}
