import { useEffect, useState } from "react";
import { Navigate, useParams } from "react-router-dom";
import { Calculator } from "lucide-react";
import api from "../api";
import Layout from "../components/Layout";
import { mensajeError } from "../utils/errores";
import { fecha, limpiar, pesos } from "../utils/formato";
import { Campo, inputStyle, thStyle, tdStyle, botonSecundario, enlace, mensajeErrorEstilo } from "../components/ui";

const TITULOS = {
  laboral: "Liquidación laboral",
  credito: "Liquidación de crédito",
  cuotas: "Liquidación de cuotas de administración",
  alimentos: "Liquidación de alimentos",
};
const AYUDA = {
  laboral: "Cesantías, intereses, prima, vacaciones e indemnización por despido. Digite el salario mínimo y el auxilio de transporte vigentes.",
  credito: "Capital más intereses de mora, con tasas por período y abonos. Digite la tasa efectiva anual certificada para cada período.",
  cuotas: "Cuotas de administración vencidas (propiedad horizontal) con interés de mora. Digite la tasa EA que corresponda (Ley 675, art. 30).",
  alimentos: "Cuotas alimentarias atrasadas con incremento anual, mesadas adicionales e interés opcional. Verifique los valores con la sentencia o el acuerdo.",
};

const INICIAL = {
  laboral: {
    salario_mensual: "", auxilio_transporte: "", fecha_inicio: "", fecha_fin: "", desde_cesantias: "", desde_prima: "",
    desde_vacaciones: "", dias_vacaciones_disfrutados: "", salarios_pendientes_dias: "", deducciones: "",
    indemnizacion: false, tipo_contrato: "indefinido", fecha_fin_pactada: "", salario_minimo: "",
  },
  credito: { capital: "", fecha_inicio_mora: "", fecha_corte: "", modo: "unica", tasa_ea: "", periodos: [], abonos: [], costas: "", otros: "" },
  cuotas: { valor_cuota: "", mes_inicial: "", mes_final: "", dia_vencimiento: "", fecha_corte: "", tasa_ea: "", extraordinarias: [], abonos_total: "" },
  alimentos: { valor_cuota: "", mes_inicial: "", mes_final: "", dia_vencimiento: "", fecha_corte: "", tasa_ea: "", incremento_anual: "", adicionales: [], abonos_total: "" },
};

// "2026-03" (input month) -> "2026-03-01"
const mesAFecha = (m) => (m ? `${m}-01` : "");

function construirDatos(tipo, f) {
  if (tipo === "laboral") {
    const d = { ...f };
    if (!d.indemnizacion) {
      delete d.tipo_contrato; delete d.fecha_fin_pactada; delete d.salario_minimo;
    } else if (d.tipo_contrato === "fijo") {
      delete d.salario_minimo;
    } else {
      delete d.fecha_fin_pactada;
    }
    return limpiar(d);
  }
  if (tipo === "credito") {
    const d = { capital: f.capital, fecha_inicio_mora: f.fecha_inicio_mora, fecha_corte: f.fecha_corte, costas: f.costas, otros: f.otros };
    if (f.modo === "unica") d.tasa_ea = f.tasa_ea;
    else d.periodos = f.periodos.map(limpiar);
    if (f.abonos.length) d.abonos = f.abonos.map(limpiar);
    return limpiar(d);
  }
  if (tipo === "alimentos") {
    const d = {
      valor_cuota: f.valor_cuota, mes_inicial: mesAFecha(f.mes_inicial), mes_final: mesAFecha(f.mes_final),
      dia_vencimiento: f.dia_vencimiento, fecha_corte: f.fecha_corte, tasa_ea: f.tasa_ea,
      incremento_anual: f.incremento_anual, abonos_total: f.abonos_total,
    };
    if (f.adicionales.length) d.adicionales = f.adicionales.map(limpiar);
    return limpiar(d);
  }
  const d = {
    valor_cuota: f.valor_cuota, mes_inicial: mesAFecha(f.mes_inicial), mes_final: mesAFecha(f.mes_final),
    dia_vencimiento: f.dia_vencimiento, fecha_corte: f.fecha_corte, tasa_ea: f.tasa_ea, abonos_total: f.abonos_total,
  };
  if (f.extraordinarias.length) d.extraordinarias = f.extraordinarias.map(limpiar);
  return limpiar(d);
}

export default function Liquidacion() {
  const { tipo } = useParams();
  if (!TITULOS[tipo]) return <Navigate to="/liquidacion/laboral" replace />;
  // `key` reinicia el formulario al cambiar de tipo desde el menú
  return <PantallaLiquidacion key={tipo} tipo={tipo} />;
}

function PantallaLiquidacion({ tipo }) {
  const [f, setF] = useState(INICIAL[tipo]);
  const [resultado, setResultado] = useState(null);
  const [payload, setPayload] = useState(null);
  const [error, setError] = useState("");
  const [calculando, setCalculando] = useState(false);
  const [guardadas, setGuardadas] = useState([]);
  const [expedientes, setExpedientes] = useState([]);
  const [guardando, setGuardando] = useState(false);
  const [referencia, setReferencia] = useState("");
  const [expedienteId, setExpedienteId] = useState("");
  const [aviso, setAviso] = useState("");

  const cargarGuardadas = () =>
    api.get("/liquidaciones/").then((r) => setGuardadas(r.data.filter((x) => x.tipo === tipo))).catch(() => {});

  useEffect(() => {
    cargarGuardadas();
    api.get("/expedientes/").then((r) => setExpedientes(r.data)).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const set = (k) => (e) => setF({ ...f, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value });
  const setFila = (lista, i, k, v) => setF({ ...f, [lista]: f[lista].map((x, j) => (j === i ? { ...x, [k]: v } : x)) });
  const agregarFila = (lista, vacia) => setF({ ...f, [lista]: [...f[lista], vacia] });
  const quitarFila = (lista, i) => setF({ ...f, [lista]: f[lista].filter((_, j) => j !== i) });

  const calcular = async (e) => {
    e.preventDefault();
    setError("");
    setAviso("");
    setCalculando(true);
    try {
      const datos = construirDatos(tipo, f);
      const r = await api.post("/liquidaciones/calcular/", { tipo, datos });
      setResultado(r.data.resultado);
      setPayload(datos);
    } catch (err) {
      setResultado(null);
      setError(mensajeError(err, "No se pudo calcular."));
    } finally {
      setCalculando(false);
    }
  };

  const guardar = async () => {
    setAviso("");
    if (referencia.trim().length < 3) return setAviso("Escriba un nombre o asunto para guardar (por ejemplo, “Pagaré Pérez”).");
    setGuardando(true);
    try {
      const cuerpo = { tipo, referencia: referencia.trim(), datos: payload };
      if (expedienteId) cuerpo.expediente = Number(expedienteId);
      await api.post("/liquidaciones/", cuerpo);
      setReferencia("");
      setAviso("✅ Liquidación guardada.");
      cargarGuardadas();
    } catch (err) {
      setAviso(`❌ ${mensajeError(err, "No se pudo guardar.")}`);
    } finally {
      setGuardando(false);
    }
  };

  const eliminar = async (x) => {
    if (!window.confirm(`¿Eliminar la liquidación “${x.referencia}”?`)) return;
    try {
      await api.delete(`/liquidaciones/${x.id}/`);
      cargarGuardadas();
    } catch (err) {
      alert(mensajeError(err, "No se pudo eliminar."));
    }
  };

  const ver = (x) => {
    setResultado(x.resultado);
    setPayload(null);
    setAviso(`Mostrando “${x.referencia}” (guardada el ${fecha(x.creado_en)}). Para guardar otra, calcule de nuevo.`);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const fila2 = { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 14px" };

  return (
    <Layout>
      <style>{"@media print { aside, .no-imprimir { display: none !important; } }"}</style>
      <div style={{ minHeight: "100vh", background: "#f4f7fb", fontFamily: "sans-serif" }}>
        <header className="no-imprimir" style={{ background: "white", padding: "16px 32px", borderBottom: "1px solid #e9edf2" }}>
          <div style={{ fontSize: "20px", fontWeight: "bold", display: "flex", alignItems: "center", gap: "10px" }}>
            <Calculator size={22} color="#0a1a2b" />
            {TITULOS[tipo]}
          </div>
          <div style={{ color: "#6b7f96", fontSize: "13px", marginTop: "4px" }}>{AYUDA[tipo]}</div>
        </header>

        <main style={{ padding: "32px", display: "grid", gridTemplateColumns: "minmax(320px, 420px) 1fr", gap: "24px", alignItems: "start" }}>
          <form className="no-imprimir" onSubmit={calcular} style={{ background: "white", borderRadius: "16px", border: "1px solid #eef2f6", padding: "24px" }}>
            {error && <p style={mensajeErrorEstilo}>{error}</p>}

            {tipo === "laboral" && (
              <>
                <div style={fila2}>
                  <Campo label="Salario mensual"><input type="number" min="1" step="any" required value={f.salario_mensual} onChange={set("salario_mensual")} style={inputStyle} /></Campo>
                  <Campo label="Auxilio de transporte"><input type="number" min="0" step="any" value={f.auxilio_transporte} onChange={set("auxilio_transporte")} style={inputStyle} /></Campo>
                  <Campo label="Fecha de ingreso"><input type="date" required value={f.fecha_inicio} onChange={set("fecha_inicio")} style={inputStyle} /></Campo>
                  <Campo label="Fecha de retiro"><input type="date" required value={f.fecha_fin} onChange={set("fecha_fin")} style={inputStyle} /></Campo>
                </div>
                <div style={fila2}>
                  <Campo label="Días de salario pendientes"><input type="number" min="0" max="60" value={f.salarios_pendientes_dias} onChange={set("salarios_pendientes_dias")} style={inputStyle} /></Campo>
                  <Campo label="Vacaciones ya disfrutadas (días hábiles)"><input type="number" min="0" value={f.dias_vacaciones_disfrutados} onChange={set("dias_vacaciones_disfrutados")} style={inputStyle} /></Campo>
                  <Campo label="Deducciones / pagos ya hechos"><input type="number" min="0" step="any" value={f.deducciones} onChange={set("deducciones")} style={inputStyle} /></Campo>
                </div>
                <details style={{ marginBottom: "14px" }}>
                  <summary style={{ cursor: "pointer", fontSize: "13px", color: "#1f3b57" }}>Ajustar los períodos liquidados</summary>
                  <p style={{ fontSize: "12px", color: "#6b7f96" }}>
                    Si no se indica, cesantías e intereses van desde el 1 de enero del año de retiro, la prima desde el inicio del semestre y las vacaciones desde el ingreso.
                  </p>
                  <div style={fila2}>
                    <Campo label="Cesantías desde"><input type="date" value={f.desde_cesantias} onChange={set("desde_cesantias")} style={inputStyle} /></Campo>
                    <Campo label="Prima desde"><input type="date" value={f.desde_prima} onChange={set("desde_prima")} style={inputStyle} /></Campo>
                    <Campo label="Vacaciones desde"><input type="date" value={f.desde_vacaciones} onChange={set("desde_vacaciones")} style={inputStyle} /></Campo>
                  </div>
                </details>
                <label style={{ fontSize: "14px", display: "flex", gap: "8px", alignItems: "center", marginBottom: "10px" }}>
                  <input type="checkbox" checked={f.indemnizacion} onChange={set("indemnizacion")} />
                  Incluir indemnización por despido sin justa causa
                </label>
                {f.indemnizacion && (
                  <div style={{ background: "#f8fafc", padding: "12px", borderRadius: "10px", marginBottom: "14px" }}>
                    <Campo label="Tipo de contrato">
                      <select value={f.tipo_contrato} onChange={set("tipo_contrato")} style={inputStyle}>
                        <option value="indefinido">Término indefinido</option>
                        <option value="fijo">Término fijo</option>
                      </select>
                    </Campo>
                    {f.tipo_contrato === "fijo" ? (
                      <Campo label="Fecha de terminación pactada"><input type="date" required value={f.fecha_fin_pactada} onChange={set("fecha_fin_pactada")} style={inputStyle} /></Campo>
                    ) : (
                      <Campo label="Salario mínimo vigente" ayuda="Define si el salario supera 10 salarios mínimos.">
                        <input type="number" min="1" step="any" required value={f.salario_minimo} onChange={set("salario_minimo")} style={inputStyle} />
                      </Campo>
                    )}
                  </div>
                )}
              </>
            )}

            {tipo === "credito" && (
              <>
                <Campo label="Capital"><input type="number" min="1" step="any" required value={f.capital} onChange={set("capital")} style={inputStyle} /></Campo>
                <div style={fila2}>
                  <Campo label="Inicio de la mora"><input type="date" required value={f.fecha_inicio_mora} onChange={set("fecha_inicio_mora")} style={inputStyle} /></Campo>
                  <Campo label="Fecha de corte"><input type="date" required value={f.fecha_corte} onChange={set("fecha_corte")} style={inputStyle} /></Campo>
                </div>
                <Campo label="Tasa de interés">
                  <select value={f.modo} onChange={set("modo")} style={inputStyle}>
                    <option value="unica">Una sola tasa EA para todo el período</option>
                    <option value="periodos">Tasas por período (según certificación)</option>
                  </select>
                </Campo>
                {f.modo === "unica" ? (
                  <Campo label="Tasa efectiva anual (%)"><input type="number" min="0" max="200" step="any" required value={f.tasa_ea} onChange={set("tasa_ea")} style={inputStyle} /></Campo>
                ) : (
                  <div style={{ marginBottom: "14px" }}>
                    {f.periodos.map((p, i) => (
                      <div key={i} style={{ display: "grid", gridTemplateColumns: "1fr 1fr 70px 24px", gap: "6px", marginBottom: "6px" }}>
                        <input type="date" required value={p.desde} onChange={(e) => setFila("periodos", i, "desde", e.target.value)} style={inputStyle} title="Desde" />
                        <input type="date" required value={p.hasta} onChange={(e) => setFila("periodos", i, "hasta", e.target.value)} style={inputStyle} title="Hasta" />
                        <input type="number" min="0" max="200" step="any" required placeholder="% EA" value={p.tasa_ea} onChange={(e) => setFila("periodos", i, "tasa_ea", e.target.value)} style={inputStyle} />
                        <button type="button" onClick={() => quitarFila("periodos", i)} style={{ border: "none", background: "none", color: "#c73a3a", cursor: "pointer" }}>✕</button>
                      </div>
                    ))}
                    <button type="button" onClick={() => agregarFila("periodos", { desde: "", hasta: "", tasa_ea: "" })} style={botonSecundario}>+ Agregar período</button>
                    <div style={{ fontSize: "12px", color: "#6b7f96", marginTop: "4px" }}>Cada período empieza el día siguiente al anterior y deben cubrir hasta la fecha de corte.</div>
                  </div>
                )}
                <div style={{ marginBottom: "14px" }}>
                  <div style={{ fontSize: "13px", color: "#6b7f96", marginBottom: "4px" }}>Abonos (opcional)</div>
                  {f.abonos.map((a, i) => (
                    <div key={i} style={{ display: "grid", gridTemplateColumns: "1fr 1fr 24px", gap: "6px", marginBottom: "6px" }}>
                      <input type="date" required value={a.fecha} onChange={(e) => setFila("abonos", i, "fecha", e.target.value)} style={inputStyle} />
                      <input type="number" min="1" step="any" required placeholder="Valor" value={a.valor} onChange={(e) => setFila("abonos", i, "valor", e.target.value)} style={inputStyle} />
                      <button type="button" onClick={() => quitarFila("abonos", i)} style={{ border: "none", background: "none", color: "#c73a3a", cursor: "pointer" }}>✕</button>
                    </div>
                  ))}
                  <button type="button" onClick={() => agregarFila("abonos", { fecha: "", valor: "" })} style={botonSecundario}>+ Agregar abono</button>
                </div>
                <div style={fila2}>
                  <Campo label="Costas / agencias en derecho"><input type="number" min="0" step="any" value={f.costas} onChange={set("costas")} style={inputStyle} /></Campo>
                  <Campo label="Otros conceptos"><input type="number" min="0" step="any" value={f.otros} onChange={set("otros")} style={inputStyle} /></Campo>
                </div>
              </>
            )}

            {tipo === "cuotas" && (
              <>
                <div style={fila2}>
                  <Campo label="Valor de la cuota mensual"><input type="number" min="1" step="any" required value={f.valor_cuota} onChange={set("valor_cuota")} style={inputStyle} /></Campo>
                  <Campo label="Día de vencimiento (1–28)"><input type="number" min="1" max="28" required value={f.dia_vencimiento} onChange={set("dia_vencimiento")} style={inputStyle} /></Campo>
                  <Campo label="Primera cuota adeudada"><input type="month" required value={f.mes_inicial} onChange={set("mes_inicial")} style={inputStyle} /></Campo>
                  <Campo label="Última cuota"><input type="month" required value={f.mes_final} onChange={set("mes_final")} style={inputStyle} /></Campo>
                  <Campo label="Fecha de corte"><input type="date" required value={f.fecha_corte} onChange={set("fecha_corte")} style={inputStyle} /></Campo>
                  <Campo label="Tasa de mora EA (%)"><input type="number" min="0" max="200" step="any" required value={f.tasa_ea} onChange={set("tasa_ea")} style={inputStyle} /></Campo>
                </div>
                <div style={{ marginBottom: "14px" }}>
                  <div style={{ fontSize: "13px", color: "#6b7f96", marginBottom: "4px" }}>Cuotas extraordinarias (opcional)</div>
                  {f.extraordinarias.map((x, i) => (
                    <div key={i} style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr 1fr 24px", gap: "6px", marginBottom: "6px" }}>
                      <input type="text" placeholder="Concepto" value={x.concepto} onChange={(e) => setFila("extraordinarias", i, "concepto", e.target.value)} style={inputStyle} />
                      <input type="date" required value={x.fecha_vencimiento} onChange={(e) => setFila("extraordinarias", i, "fecha_vencimiento", e.target.value)} style={inputStyle} />
                      <input type="number" min="1" step="any" required placeholder="Valor" value={x.valor} onChange={(e) => setFila("extraordinarias", i, "valor", e.target.value)} style={inputStyle} />
                      <button type="button" onClick={() => quitarFila("extraordinarias", i)} style={{ border: "none", background: "none", color: "#c73a3a", cursor: "pointer" }}>✕</button>
                    </div>
                  ))}
                  <button type="button" onClick={() => agregarFila("extraordinarias", { concepto: "", fecha_vencimiento: "", valor: "" })} style={botonSecundario}>+ Agregar cuota extraordinaria</button>
                </div>
                <Campo label="Abonos ya recibidos (total)"><input type="number" min="0" step="any" value={f.abonos_total} onChange={set("abonos_total")} style={inputStyle} /></Campo>
              </>
            )}

            {tipo === "alimentos" && (
              <>
                <div style={fila2}>
                  <Campo label="Valor de la cuota mensual"><input type="number" min="1" step="any" required value={f.valor_cuota} onChange={set("valor_cuota")} style={inputStyle} /></Campo>
                  <Campo label="Día de vencimiento (1–28)"><input type="number" min="1" max="28" required value={f.dia_vencimiento} onChange={set("dia_vencimiento")} style={inputStyle} /></Campo>
                  <Campo label="Primera cuota adeudada"><input type="month" required value={f.mes_inicial} onChange={set("mes_inicial")} style={inputStyle} /></Campo>
                  <Campo label="Última cuota"><input type="month" required value={f.mes_final} onChange={set("mes_final")} style={inputStyle} /></Campo>
                  <Campo label="Fecha de corte"><input type="date" required value={f.fecha_corte} onChange={set("fecha_corte")} style={inputStyle} /></Campo>
                  <Campo label="Incremento anual (%)" ayuda="Se aplica cada 1 de enero. 0 si no hay."><input type="number" min="0" max="100" step="any" value={f.incremento_anual} onChange={set("incremento_anual")} style={inputStyle} /></Campo>
                </div>
                <Campo label="Tasa de interés EA (%)" ayuda="Déjela vacía o en 0 si no se cobra interés.">
                  <input type="number" min="0" max="200" step="any" value={f.tasa_ea} onChange={set("tasa_ea")} style={inputStyle} />
                </Campo>
                <div style={{ marginBottom: "14px" }}>
                  <div style={{ fontSize: "13px", color: "#6b7f96", marginBottom: "4px" }}>Mesadas adicionales (prima, Navidad, útiles…)</div>
                  {f.adicionales.map((x, i) => (
                    <div key={i} style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr 1fr 24px", gap: "6px", marginBottom: "6px" }}>
                      <input type="text" placeholder="Concepto" value={x.concepto} onChange={(e) => setFila("adicionales", i, "concepto", e.target.value)} style={inputStyle} />
                      <input type="date" required value={x.fecha_vencimiento} onChange={(e) => setFila("adicionales", i, "fecha_vencimiento", e.target.value)} style={inputStyle} />
                      <input type="number" min="1" step="any" required placeholder="Valor" value={x.valor} onChange={(e) => setFila("adicionales", i, "valor", e.target.value)} style={inputStyle} />
                      <button type="button" onClick={() => quitarFila("adicionales", i)} style={{ border: "none", background: "none", color: "#c73a3a", cursor: "pointer" }}>✕</button>
                    </div>
                  ))}
                  <button type="button" onClick={() => agregarFila("adicionales", { concepto: "", fecha_vencimiento: "", valor: "" })} style={botonSecundario}>+ Agregar mesada adicional</button>
                </div>
                <Campo label="Abonos ya recibidos (total)"><input type="number" min="0" step="any" value={f.abonos_total} onChange={set("abonos_total")} style={inputStyle} /></Campo>
              </>
            )}

            <button type="submit" disabled={calculando} style={{ width: "100%", padding: "12px", borderRadius: "10px", border: "none", background: "#0a1a2b", color: "white", cursor: "pointer", fontWeight: 600 }}>
              {calculando ? "Calculando..." : "Calcular"}
            </button>
          </form>

          <section>
            {!resultado && (
              <div style={{ background: "white", borderRadius: "16px", border: "1px dashed #d0d9e3", padding: "40px", color: "#6b7f96", textAlign: "center" }}>
                Complete los datos y presione <strong>Calcular</strong> para ver el detalle de la liquidación.
              </div>
            )}
            {resultado && (
              <div style={{ background: "white", borderRadius: "16px", border: "1px solid #eef2f6", padding: "24px" }}>
                <Resultado r={resultado} />
                <div className="no-imprimir" style={{ marginTop: "20px", paddingTop: "16px", borderTop: "1px solid #eef2f6" }}>
                  {aviso && <p style={{ fontSize: "13px", whiteSpace: "pre-line" }}>{aviso}</p>}
                  <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "center" }}>
                    {payload && (
                      <>
                        <input type="text" placeholder="Nombre o asunto para guardar" value={referencia} onChange={(e) => setReferencia(e.target.value)} maxLength={150} style={{ ...inputStyle, width: "240px" }} />
                        <select value={expedienteId} onChange={(e) => setExpedienteId(e.target.value)} style={{ ...inputStyle, width: "220px" }}>
                          <option value="">Sin expediente</option>
                          {expedientes.map((x) => <option key={x.id} value={x.id}>{x.numero}</option>)}
                        </select>
                        <button type="button" onClick={guardar} disabled={guardando} style={{ padding: "9px 16px", borderRadius: "8px", border: "none", background: "#1b8b5e", color: "white", cursor: "pointer" }}>
                          {guardando ? "Guardando..." : "Guardar"}
                        </button>
                      </>
                    )}
                    <button type="button" onClick={() => window.print()} style={botonSecundario}>Imprimir</button>
                  </div>
                </div>
              </div>
            )}

            <div className="no-imprimir" style={{ background: "white", borderRadius: "16px", border: "1px solid #eef2f6", marginTop: "24px", overflowX: "auto" }}>
              <h3 style={{ margin: 0, padding: "18px 24px 8px", color: "#1a2c3e" }}>Liquidaciones guardadas</h3>
              {guardadas.length === 0 ? (
                <p style={{ padding: "0 24px 20px", color: "#6b7f96" }}>Aún no hay liquidaciones guardadas de este tipo.</p>
              ) : (
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
                  <thead>
                    <tr style={{ background: "#f8fafc" }}>
                      {["Nombre", "Expediente", "Total", "Fecha", "Por", "Acción"].map((h) => <th key={h} style={thStyle}>{h}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {guardadas.map((x) => (
                      <tr key={x.id} style={{ borderTop: "1px solid #f0f3f8" }}>
                        <td style={tdStyle}><strong>{x.referencia}</strong></td>
                        <td style={tdStyle}>{x.expediente_numero || "—"}</td>
                        <td style={tdStyle}>{pesos(x.total)}</td>
                        <td style={tdStyle}>{fecha(x.creado_en)}</td>
                        <td style={tdStyle}>{x.creado_por_nombre || "—"}</td>
                        <td style={tdStyle}>
                          <button style={enlace()} onClick={() => ver(x)}>Ver</button>
                          <button style={enlace("#c73a3a")} onClick={() => eliminar(x)}>Eliminar</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </section>
        </main>
      </div>
    </Layout>
  );
}

const tabla = { width: "100%", borderCollapse: "collapse", fontSize: "14px", marginBottom: "16px" };
const derecha = { ...tdStyle, textAlign: "right", whiteSpace: "nowrap" };

function Total({ etiqueta, valor, fuerte }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", padding: fuerte ? "12px 0" : "4px 0", fontWeight: fuerte ? 700 : 500, fontSize: fuerte ? "18px" : "14px", borderTop: fuerte ? "2px solid #0a1a2b" : "none" }}>
      <span>{etiqueta}</span>
      <span>{pesos(valor)}</span>
    </div>
  );
}

function Resultado({ r }) {
  return (
    <div>
      <h3 style={{ marginTop: 0 }}>Resultado</h3>

      {r.tipo === "laboral" && (
        <>
          <p style={{ color: "#6b7f96", fontSize: "13px" }}>
            Período: {fecha(r.periodo.desde)} al {fecha(r.periodo.hasta)} ({r.periodo.dias_360} días, año de 360)
          </p>
          <table style={tabla}>
            <thead><tr style={{ background: "#f8fafc" }}><th style={thStyle}>Concepto</th><th style={{ ...thStyle, textAlign: "right" }}>Días</th><th style={{ ...thStyle, textAlign: "right" }}>Valor</th></tr></thead>
            <tbody>
              {r.conceptos.map((c, i) => (
                <tr key={i} style={{ borderTop: "1px solid #f0f3f8" }}>
                  <td style={tdStyle}>
                    <strong>{c.concepto}</strong>
                    <div style={{ color: "#6b7f96", fontSize: "12px" }}>{c.formula}</div>
                  </td>
                  <td style={derecha}>{c.dias}</td>
                  <td style={derecha}>{pesos(c.valor)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <Total etiqueta="Subtotal" valor={r.subtotal} />
          {r.deducciones > 0 && <Total etiqueta="Deducciones" valor={-r.deducciones} />}
          <Total etiqueta="Total a pagar" valor={r.total} fuerte />
        </>
      )}

      {r.tipo === "credito" && (
        <>
          <table style={tabla}>
            <thead>
              <tr style={{ background: "#f8fafc" }}>
                {["Desde", "Hasta", "Días", "Tasa EA", "Tasa mensual", "Capital", "Interés"].map((h, i) => <th key={h} style={{ ...thStyle, textAlign: i > 1 ? "right" : "left" }}>{h}</th>)}
              </tr>
            </thead>
            <tbody>
              {r.tramos.map((t, i) => (
                <tr key={i} style={{ borderTop: "1px solid #f0f3f8" }}>
                  <td style={tdStyle}>{fecha(t.desde)}</td><td style={tdStyle}>{fecha(t.hasta)}</td>
                  <td style={derecha}>{t.dias}</td><td style={derecha}>{t.tasa_ea}%</td><td style={derecha}>{t.tasa_mensual}%</td>
                  <td style={derecha}>{pesos(t.capital)}</td><td style={derecha}>{pesos(t.interes)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {r.abonos.length > 0 && (
            <>
              <h4 style={{ marginBottom: "6px" }}>Abonos</h4>
              <table style={tabla}>
                <thead><tr style={{ background: "#f8fafc" }}>{["Fecha", "Valor", "A intereses", "A capital"].map((h, i) => <th key={h} style={{ ...thStyle, textAlign: i ? "right" : "left" }}>{h}</th>)}</tr></thead>
                <tbody>
                  {r.abonos.map((a, i) => (
                    <tr key={i} style={{ borderTop: "1px solid #f0f3f8" }}>
                      <td style={tdStyle}>{fecha(a.fecha)}</td><td style={derecha}>{pesos(a.valor)}</td><td style={derecha}>{pesos(a.a_intereses)}</td><td style={derecha}>{pesos(a.a_capital)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
          <Total etiqueta="Capital inicial" valor={r.capital_inicial} />
          <Total etiqueta="Capital pendiente" valor={r.capital_pendiente} />
          <Total etiqueta="Intereses causados" valor={r.intereses_causados} />
          <Total etiqueta="Intereses pagados con abonos" valor={-r.intereses_pagados} />
          <Total etiqueta="Intereses pendientes" valor={r.intereses_pendientes} />
          {r.costas > 0 && <Total etiqueta="Costas" valor={r.costas} />}
          {r.otros > 0 && <Total etiqueta="Otros conceptos" valor={r.otros} />}
          <Total etiqueta="Total a pagar" valor={r.total} fuerte />
        </>
      )}

      {(r.tipo === "cuotas" || r.tipo === "alimentos") && (
        <>
          <table style={tabla}>
            <thead>
              <tr style={{ background: "#f8fafc" }}>
                {["Concepto", "Vence", "Valor", "Días mora", "Interés", "Total"].map((h, i) => <th key={h} style={{ ...thStyle, textAlign: i > 1 ? "right" : "left" }}>{h}</th>)}
              </tr>
            </thead>
            <tbody>
              {r.filas.map((x, i) => (
                <tr key={i} style={{ borderTop: "1px solid #f0f3f8" }}>
                  <td style={tdStyle}>{x.concepto}</td><td style={tdStyle}>{fecha(x.vencimiento)}</td>
                  <td style={derecha}>{pesos(x.valor)}</td><td style={derecha}>{x.dias_mora}</td>
                  <td style={derecha}>{pesos(x.interes)}</td><td style={derecha}>{pesos(x.total)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <Total etiqueta={r.tipo === "alimentos" ? "Cuotas alimentarias adeudadas" : "Cuotas adeudadas"} valor={r.capital} />
          {(r.tipo === "cuotas" || r.intereses > 0) && <Total etiqueta="Intereses de mora" valor={r.intereses} />}
          {r.abonos > 0 && <Total etiqueta="Abonos" valor={-r.abonos} />}
          <Total etiqueta="Total a pagar" valor={r.total} fuerte />
        </>
      )}

      <div style={{ marginTop: "16px", fontSize: "12px", color: "#6b7f96" }}>
        <strong>Supuestos</strong>
        <ul style={{ margin: "4px 0 8px", paddingLeft: "18px" }}>{r.supuestos.map((s, i) => <li key={i}>{s}</li>)}</ul>
        <em>{r.advertencia}</em>
      </div>
    </div>
  );
}
