import { useEffect, useState } from "react";
import { Wallet } from "lucide-react";
import api from "../api";
import { mensajeError } from "../utils/errores";
import { pesos, fecha } from "../utils/formato";
import Layout from "../components/Layout";
import {
  Encabezado, EnlaceExpedientes, Modal, Campo, Dato, Etiqueta, inputStyle, thStyle, tdStyle,
  botonPrimario, botonSecundario, enlace, mensajeErrorEstilo,
} from "../components/ui";

const ESTADOS = {
  vigente: { texto: "Vigente", bg: "#e3effb", color: "#1f5a99" },
  en_mora: { texto: "En mora", bg: "#fde8e8", color: "#c73a3a" },
  cumplido: { texto: "Cumplido", bg: "#e0f3ea", color: "#1b8b5e" },
  cancelado: { texto: "Cancelado", bg: "#eceff3", color: "#6b7f96" },
};

const hoyISO = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};

const FORM_VACIO = {
  expediente: "", deudor: "", concepto: "", valor_total: "", fecha_acuerdo: hoyISO(),
  num_cuotas: "1", fecha_primera_cuota: "", observaciones: "",
};

export default function Acuerdos() {
  const [acuerdos, setAcuerdos] = useState([]);
  const [expedientes, setExpedientes] = useState([]);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(true);
  const [busqueda, setBusqueda] = useState("");
  const [mostrarForm, setMostrarForm] = useState(false);
  const [editandoId, setEditandoId] = useState(null);
  const [form, setForm] = useState(FORM_VACIO);
  const [formError, setFormError] = useState("");
  const [guardando, setGuardando] = useState(false);
  const [detalleId, setDetalleId] = useState(null);
  const [fechaPago, setFechaPago] = useState(hoyISO());
  const [errorDetalle, setErrorDetalle] = useState("");

  const cargar = () => {
    setCargando(true);
    api
      .get("/acuerdos-pago/")
      .then((r) => setAcuerdos(r.data))
      .catch(() => setError("No se pudieron cargar los acuerdos de pago."))
      .finally(() => setCargando(false));
  };

  useEffect(() => {
    cargar();
    api.get("/expedientes/").then((r) => setExpedientes(r.data)).catch(() => {});
  }, []);

  const detalle = acuerdos.find((a) => a.id === detalleId) || null;
  const reemplazar = (nuevo) => setAcuerdos((prev) => prev.map((a) => (a.id === nuevo.id ? nuevo : a)));

  const filtrados = acuerdos.filter((a) => {
    const t = busqueda.toLowerCase();
    return a.expediente_numero.toLowerCase().includes(t) || a.deudor.toLowerCase().includes(t) || a.concepto.toLowerCase().includes(t);
  });

  const activos = acuerdos.filter((a) => a.estado_actual === "vigente" || a.estado_actual === "en_mora");
  const enMora = acuerdos.filter((a) => a.estado_actual === "en_mora").length;
  const saldoPorCobrar = activos.reduce((s, a) => s + Number(a.saldo), 0);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const abrirNuevo = () => {
    setForm({ ...FORM_VACIO, fecha_acuerdo: hoyISO() });
    setEditandoId(null);
    setFormError("");
    setMostrarForm(true);
  };

  const abrirEditar = (a) => {
    setForm({ ...FORM_VACIO, deudor: a.deudor, concepto: a.concepto, fecha_acuerdo: a.fecha_acuerdo, observaciones: a.observaciones || "" });
    setEditandoId(a.id);
    setFormError("");
    setMostrarForm(true);
  };

  const cerrarForm = () => {
    setMostrarForm(false);
    setEditandoId(null);
    setFormError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError("");
    setGuardando(true);
    try {
      if (editandoId) {
        const { deudor, concepto, fecha_acuerdo, observaciones } = form;
        await api.patch(`/acuerdos-pago/${editandoId}/`, { deudor, concepto, fecha_acuerdo, observaciones });
      } else {
        await api.post("/acuerdos-pago/", { ...form, num_cuotas: Number(form.num_cuotas) });
      }
      cerrarForm();
      cargar();
    } catch (err) {
      setFormError(mensajeError(err, "No se pudo guardar el acuerdo."));
    } finally {
      setGuardando(false);
    }
  };

  const cambiarEstado = async (a, estado) => {
    const msg = estado === "cancelado" ? `¿Cancelar el acuerdo "${a.concepto}"? Ya no aparecerá como pendiente.` : `¿Reactivar el acuerdo "${a.concepto}"?`;
    if (!window.confirm(msg)) return;
    try {
      const r = await api.patch(`/acuerdos-pago/${a.id}/`, { estado });
      reemplazar(r.data);
    } catch (err) {
      alert(mensajeError(err, "No se pudo cambiar el estado."));
    }
  };

  const eliminar = async (a) => {
    if (!window.confirm(`¿Eliminar el acuerdo "${a.concepto}" y todas sus cuotas?`)) return;
    try {
      await api.delete(`/acuerdos-pago/${a.id}/`);
      setAcuerdos((prev) => prev.filter((x) => x.id !== a.id));
      if (detalleId === a.id) setDetalleId(null);
    } catch (err) {
      alert(mensajeError(err, "No se pudo eliminar el acuerdo."));
    }
  };

  const movimientoCuota = async (accion, cuota) => {
    setErrorDetalle("");
    try {
      const datos = accion === "pagar" ? { cuota: cuota.id, fecha_pago: fechaPago } : { cuota: cuota.id };
      const r = await api.post(`/acuerdos-pago/${detalle.id}/${accion}/`, datos);
      reemplazar(r.data);
    } catch (err) {
      setErrorDetalle(mensajeError(err, "No se pudo actualizar la cuota."));
    }
  };

  return (
    <Layout>
      <div style={{ minHeight: "100vh", background: "#f4f7fb", fontFamily: "sans-serif" }}>
        <Encabezado Icono={Wallet} titulo="Acuerdos de pago" busqueda={busqueda} setBusqueda={setBusqueda} placeholder="Buscar..." textoBoton="+ Nuevo acuerdo" onNuevo={abrirNuevo} />

        <main style={{ padding: "32px" }}>
          <EnlaceExpedientes />
          {error && <p style={{ color: "#c73a3a" }}>{error}</p>}
          {cargando && <p>Cargando acuerdos...</p>}

          {!cargando && !error && (
            <>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "14px", marginBottom: "18px" }}>
                <Resumen titulo="Acuerdos activos" valor={activos.length} color="#2f5d8a" />
                <Resumen titulo="En mora" valor={enMora} color="#c73a3a" />
                <Resumen titulo="Saldo por cobrar" valor={pesos(saldoPorCobrar)} color="#8a7a2b" />
              </div>

              <div style={{ background: "white", borderRadius: "16px", border: "1px solid #eef2f6", overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
                  <thead>
                    <tr style={{ background: "#f8fafc" }}>
                      <th style={thStyle}>Expediente</th>
                      <th style={thStyle}>Deudor y concepto</th>
                      <th style={thStyle}>Valor total</th>
                      <th style={thStyle}>Pagado</th>
                      <th style={thStyle}>Saldo</th>
                      <th style={thStyle}>Estado</th>
                      <th style={thStyle}>Acción</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtrados.map((a) => {
                      const e = ESTADOS[a.estado_actual];
                      const pagadas = a.cuotas.filter((c) => c.pagada).length;
                      return (
                        <tr key={a.id} style={{ borderTop: "1px solid #f0f3f8" }}>
                          <td style={tdStyle}>{a.expediente_numero}</td>
                          <td style={tdStyle}>
                            <strong>{a.deudor}</strong>
                            <div style={{ color: "#6b7f96", fontSize: "12px" }}>{a.concepto} · {pagadas}/{a.cuotas.length} cuotas</div>
                          </td>
                          <td style={tdStyle}>{pesos(a.valor_total)}</td>
                          <td style={tdStyle}>{pesos(a.total_pagado)}</td>
                          <td style={tdStyle}><strong>{pesos(a.saldo)}</strong></td>
                          <td style={tdStyle}><Etiqueta texto={e.texto} bg={e.bg} color={e.color} /></td>
                          <td style={tdStyle}>
                            <button type="button" onClick={() => { setDetalleId(a.id); setErrorDetalle(""); setFechaPago(hoyISO()); }} style={enlace()}>Ver cuotas</button>
                            <button type="button" onClick={() => abrirEditar(a)} style={enlace("#a8681a")}>Editar</button>
                            {a.estado === "cancelado" ? (
                              <button type="button" onClick={() => cambiarEstado(a, "vigente")} style={enlace("#1b8b5e")}>Reactivar</button>
                            ) : (
                              <button type="button" onClick={() => cambiarEstado(a, "cancelado")} style={enlace("#6b7f96")}>Cancelar</button>
                            )}
                            <button type="button" onClick={() => eliminar(a)} style={enlace("#c73a3a")}>Eliminar</button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                {filtrados.length === 0 && <p style={{ padding: "24px", color: "#6b7f96" }}>No hay acuerdos de pago que coincidan.</p>}
              </div>
            </>
          )}
        </main>

        {mostrarForm && (
          <Modal onClose={cerrarForm} comoFormulario onSubmit={handleSubmit} ancho={460}>
            <h2 style={{ marginBottom: "16px" }}>{editandoId ? "Editar acuerdo de pago" : "Nuevo acuerdo de pago"}</h2>
            {formError && <p style={mensajeErrorEstilo}>{formError}</p>}

            {!editandoId && (
              <Campo label="Expediente">
                <select name="expediente" value={form.expediente} onChange={handleChange} required style={inputStyle}>
                  <option value="">Selecciona un expediente</option>
                  {expedientes.map((x) => (
                    <option key={x.id} value={x.id}>{x.numero} — {x.demandante} vs. {x.demandado}</option>
                  ))}
                </select>
              </Campo>
            )}
            <Campo label="Deudor (quien se obliga a pagar)">
              <input name="deudor" value={form.deudor} onChange={handleChange} required maxLength={200} style={inputStyle} />
            </Campo>
            <Campo label="Concepto">
              <input name="concepto" value={form.concepto} onChange={handleChange} required maxLength={200} placeholder="Ej.: pago de condena, honorarios, canon adeudado" style={inputStyle} />
            </Campo>
            {!editandoId && (
              <Campo label="Valor total (COP)">
                <input type="number" name="valor_total" value={form.valor_total} onChange={handleChange} required min="1" step="0.01" style={inputStyle} />
              </Campo>
            )}
            <Campo label="Fecha del acuerdo">
              <input type="date" name="fecha_acuerdo" value={form.fecha_acuerdo} onChange={handleChange} required style={inputStyle} />
            </Campo>
            {!editandoId && (
              <div style={{ display: "flex", gap: "12px" }}>
                <div style={{ flex: 1 }}>
                  <Campo label="Número de cuotas">
                    <input type="number" name="num_cuotas" value={form.num_cuotas} onChange={handleChange} required min="1" max="120" style={inputStyle} />
                  </Campo>
                </div>
                <div style={{ flex: 1 }}>
                  <Campo label="Vence la primera cuota">
                    <input type="date" name="fecha_primera_cuota" value={form.fecha_primera_cuota} onChange={handleChange} required style={inputStyle} />
                  </Campo>
                </div>
              </div>
            )}
            {!editandoId && <p style={{ fontSize: "12px", color: "#6b7f96", marginTop: "-6px" }}>Las cuotas se reparten en partes iguales, una por mes. El valor y las cuotas no se pueden cambiar después: si el acuerdo cambia, cancélelo y registre uno nuevo.</p>}
            <Campo label="Observaciones">
              <textarea name="observaciones" value={form.observaciones} onChange={handleChange} style={{ ...inputStyle, minHeight: "70px", resize: "vertical" }} />
            </Campo>

            <div style={{ display: "flex", gap: "10px", marginTop: "20px" }}>
              <button type="button" onClick={cerrarForm} style={{ ...botonSecundario, flex: 1 }}>Cancelar</button>
              <button type="submit" disabled={guardando} style={{ ...botonPrimario, flex: 1, borderRadius: "8px" }}>{guardando ? "Guardando..." : "Guardar"}</button>
            </div>
          </Modal>
        )}

        {detalle && (
          <Modal onClose={() => setDetalleId(null)} ancho={600}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h2 style={{ display: "flex", alignItems: "center", gap: "8px" }}><Wallet size={20} /> Acuerdo de pago</h2>
              <span onClick={() => setDetalleId(null)} style={{ cursor: "pointer", fontSize: "22px" }}>&times;</span>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px", marginBottom: "18px" }}>
              <Dato label="Expediente" value={detalle.expediente_numero} />
              <Dato label="Estado" value={ESTADOS[detalle.estado_actual].texto} />
              <Dato label="Deudor" value={detalle.deudor} />
              <Dato label="Concepto" value={detalle.concepto} />
              <Dato label="Valor total" value={pesos(detalle.valor_total)} />
              <Dato label="Saldo pendiente" value={pesos(detalle.saldo)} />
              <Dato label="Fecha del acuerdo" value={fecha(detalle.fecha_acuerdo)} />
              <Dato label="Observaciones" value={detalle.observaciones} />
            </div>

            <h3 style={{ marginBottom: "8px" }}>Cuotas</h3>
            {detalle.estado !== "cancelado" && (
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "10px", fontSize: "13px", color: "#6b7f96" }}>
                Fecha de pago al marcar una cuota:
                <input type="date" value={fechaPago} max={hoyISO()} onChange={(e) => setFechaPago(e.target.value)} style={{ ...inputStyle, width: "auto" }} />
              </div>
            )}
            {errorDetalle && <p style={mensajeErrorEstilo}>{errorDetalle}</p>}
            {detalle.cuotas.map((c) => (
              <div key={c.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "10px", padding: "10px 0", borderTop: "1px solid #f0f3f7", fontSize: "14px" }}>
                <span>
                  <strong>Cuota {c.numero}</strong> · {pesos(c.valor)}
                  <div style={{ fontSize: "12px", color: c.en_mora ? "#c73a3a" : "#6b7f96" }}>
                    Vence {fecha(c.fecha_vencimiento)}{c.en_mora ? " · en mora" : ""}{c.pagada ? ` · pagada el ${fecha(c.fecha_pago)}` : ""}
                  </div>
                </span>
                {detalle.estado !== "cancelado" && (c.pagada ? (
                  <button type="button" onClick={() => movimientoCuota("reabrir", c)} style={{ padding: "4px 10px", borderRadius: "6px", border: "none", background: "#eceff3", color: "#51667d", cursor: "pointer" }}>Deshacer pago</button>
                ) : (
                  <button type="button" onClick={() => movimientoCuota("pagar", c)} style={{ padding: "4px 10px", borderRadius: "6px", border: "none", background: "#e0f3ea", color: "#1b8b5e", cursor: "pointer", fontWeight: 600 }}>Registrar pago</button>
                ))}
              </div>
            ))}
          </Modal>
        )}
      </div>
    </Layout>
  );
}

function Resumen({ titulo, valor, color }) {
  return (
    <div style={{ background: "white", border: `1px solid ${color}33`, borderLeft: `5px solid ${color}`, borderRadius: "14px", padding: "14px 18px" }}>
      <div style={{ fontSize: "24px", fontWeight: 700, color }}>{valor}</div>
      <div style={{ fontSize: "13px", color: "#51667d" }}>{titulo}</div>
    </div>
  );
}
