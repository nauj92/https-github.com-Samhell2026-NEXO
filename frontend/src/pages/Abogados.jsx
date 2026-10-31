import { useEffect, useState } from "react";
import { Users } from "lucide-react";
import api from "../api";
import Layout from "../components/Layout";
import { mensajeError } from "../utils/errores";

const ROLES = [
  ["administrador", "Administrador"],
  ["socio_director", "Socio Director"],
  ["abogado", "Abogado"],
  ["secretario_juridico", "Secretario(a) Jurídico"],
  ["escribiente", "Escribiente"],
  ["cliente", "Cliente"],
];

// Contraseña temporal aleatoria (12 caracteres, sin símbolos ambiguos)
const generarClave = () => {
  const letras = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789";
  const a = new Uint32Array(12);
  window.crypto.getRandomValues(a);
  return Array.from(a, (n) => letras[n % letras.length]).join("") + "#7";
};

const vacio = { username: "", first_name: "", last_name: "", email: "", telefono: "", cedula: "", tarjeta_profesional: "", rol: "abogado", password: "" };

const input = { width: "100%", padding: "8px 10px", border: "1px solid #d5dbe5", borderRadius: "8px", fontSize: "14px", boxSizing: "border-box" };
const label = { fontSize: "12px", fontWeight: 600, color: "#4a5a70", display: "block", marginBottom: "4px" };
const btn = (bg) => ({ background: bg, color: "white", border: "none", borderRadius: "8px", padding: "8px 14px", cursor: "pointer", fontWeight: 600, fontSize: "13px" });

export default function Abogados() {
  const [perfil, setPerfil] = useState(null);
  const [usuarios, setUsuarios] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");
  const [form, setForm] = useState(null); // null = cerrado
  const [editandoId, setEditandoId] = useState(null);
  const [formError, setFormError] = useState("");
  const [guardando, setGuardando] = useState(false);

  const directivo = !!perfil?.es_directivo;
  const administrador = !!perfil?.es_administrador; // solo el administrador crea y modifica usuarios

  const cargar = (esDirectivo = directivo) => {
    setCargando(true);
    // Administradores y socios gestionan los usuarios; el resto solo consulta el directorio de abogados.
    api
      .get(esDirectivo ? "/gestion-usuarios/" : "/usuarios/")
      .then((r) => setUsuarios(r.data.results ?? r.data))
      .catch((err) => setError(mensajeError(err, "No se pudo cargar el directorio de abogados.")))
      .finally(() => setCargando(false));
  };
  useEffect(() => {
    api
      .get("/perfil/")
      .then((r) => {
        setPerfil(r.data);
        cargar(r.data.es_directivo);
      })
      .catch((err) => {
        setError(mensajeError(err, "No se pudo cargar el perfil."));
        setCargando(false);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const abrirNuevo = () => { setForm({ ...vacio }); setEditandoId(null); setFormError(""); };
  const abrirEditar = (u) => {
    setForm({ username: u.username, first_name: u.first_name, last_name: u.last_name, email: u.email, telefono: u.telefono || "", cedula: u.cedula || "", tarjeta_profesional: u.tarjeta_profesional || "", rol: u.rol, password: "" });
    setEditandoId(u.id);
    setFormError("");
  };

  const guardar = async (e) => {
    e.preventDefault();
    setFormError("");
    if (!form.first_name.trim() || !form.last_name.trim()) return setFormError("Nombre y apellido son obligatorios.");
    if (!/^\S+@\S+\.\S+$/.test(form.email)) return setFormError("Ingrese un correo válido.");
    if (!editandoId && form.password.length < 8) return setFormError("La contraseña debe tener al menos 8 caracteres.");
    setGuardando(true);
    const datos = { ...form };
    if (!datos.password) delete datos.password;
    if (editandoId) delete datos.username;
    try {
      let creado = null;
      if (editandoId) await api.patch(`/gestion-usuarios/${editandoId}/`, datos);
      else creado = (await api.post("/gestion-usuarios/", datos)).data;
      setForm(null);
      if (editandoId) setAviso(datos.password ? "Usuario actualizado. Deberá cambiar la contraseña al ingresar." : "Usuario actualizado.");
      else if (creado?.correo_enviado) setAviso(`Usuario creado. Se envió el correo de bienvenida a ${datos.email}.`);
      else setError(`Usuario creado, pero NO se pudo enviar el correo a ${datos.email}. Entréguele el usuario y la contraseña temporal por otro medio.`);
      cargar();
    } catch (err) {
      setFormError(mensajeError(err));
    } finally {
      setGuardando(false);
    }
  };

  const alternarActivo = async (u) => {
    setAviso(""); setError("");
    try {
      await api.patch(`/gestion-usuarios/${u.id}/`, { is_active: !u.is_active });
      setAviso(u.is_active ? `${u.username} fue desactivado.` : `${u.username} fue activado.`);
      cargar();
    } catch (err) {
      setError(mensajeError(err));
    }
  };

  const desbloquear = async (u) => {
    setAviso(""); setError("");
    try {
      const r = await api.post(`/gestion-usuarios/${u.id}/desbloquear/`);
      setAviso(r.data.detail);
    } catch (err) {
      setError(mensajeError(err));
    }
  };

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  return (
    <Layout>
      <div style={{ padding: "32px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
          <h1 style={{ display: "flex", alignItems: "center", gap: "10px", color: "#0a1a2b", margin: 0 }}>
            <Users size={26} /> Abogados y usuarios
          </h1>
          {administrador && <button style={btn("#1d3f66")} onClick={abrirNuevo}>+ Nuevo usuario</button>}
        </div>

        {error && <p style={{ color: "#c73a3a", background: "#fde8e8", padding: "8px 12px", borderRadius: "8px", whiteSpace: "pre-line" }}>{error}</p>}
        {aviso && <p style={{ color: "#1d6b3a", background: "#e6f6ec", padding: "8px 12px", borderRadius: "8px" }}>{aviso}</p>}

        {cargando ? (
          <p>Cargando...</p>
        ) : (
          <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", background: "white", borderRadius: "12px", overflow: "hidden" }}>
            <thead>
              <tr style={{ background: "#f1f4f9", textAlign: "left", fontSize: "13px" }}>
                {(directivo ? ["Usuario", "Nombre", "Correo", "Cédula", "T.P.", "Rol", "Estado", "Primer ingreso", ...(administrador ? ["Acciones"] : [])] : ["Usuario", "Nombre", "Rol"]).map((h) => (
                  <th key={h} style={{ padding: "12px" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {usuarios.map((u) => (
                <tr key={u.id} style={{ borderTop: "1px solid #eef1f6", fontSize: "14px" }}>
                  <td style={{ padding: "12px" }}>{u.username}</td>
                  <td style={{ padding: "12px" }}>{u.nombre_completo}</td>
                  {directivo && <td style={{ padding: "12px" }}>{u.email}</td>}
                  {directivo && <td style={{ padding: "12px" }}>{u.cedula || "—"}</td>}
                  {directivo && <td style={{ padding: "12px" }}>{u.tarjeta_profesional || "—"}</td>}
                  <td style={{ padding: "12px" }}>{(ROLES.find((r) => r[0] === u.rol) || [])[1] || u.rol}</td>
                  {directivo && <td style={{ padding: "12px", color: u.is_active ? "#1d6b3a" : "#c73a3a" }}>{u.is_active ? "Activo" : "Inactivo"}</td>}
                  {directivo && <td style={{ padding: "12px", color: u.debe_cambiar_password || u.autorizacion_datos_pendiente ? "#a8681a" : "#1d6b3a" }}>{u.debe_cambiar_password || u.autorizacion_datos_pendiente ? "Pendiente" : "Completo"}</td>}
                  {administrador && <td style={{ padding: "12px", display: "flex", gap: "6px", flexWrap: "wrap" }}>
                    <button style={btn("#3a6ea5")} onClick={() => abrirEditar(u)}>Editar</button>
                    <button style={btn(u.is_active ? "#c73a3a" : "#2e8b57")} onClick={() => alternarActivo(u)}>
                      {u.is_active ? "Desactivar" : "Activar"}
                    </button>
                    <button style={btn("#7a8699")} onClick={() => desbloquear(u)}>Desbloquear</button>
                  </td>}
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        )}

        {administrador && form && (
          <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 50 }}>
            <form onSubmit={guardar} style={{ background: "white", padding: "28px", borderRadius: "14px", width: "420px", maxHeight: "90vh", overflowY: "auto" }}>
              <h3 style={{ marginTop: 0 }}>{editandoId ? "Editar usuario" : "Nuevo usuario"}</h3>
              {!editandoId && <p style={{ fontSize: "12px", color: "#4a5a70", marginTop: 0 }}>Se enviará un correo con el usuario y una contraseña temporal. Al ingresar, la persona deberá cambiarla y autorizar el tratamiento de sus datos.</p>}
              {formError && <p style={{ color: "#c73a3a", background: "#fde8e8", padding: "8px 12px", borderRadius: "8px", fontSize: "13px", whiteSpace: "pre-line" }}>{formError}</p>}
              <div style={{ display: "grid", gap: "12px" }}>
                <div><label style={label}>Usuario</label><input style={input} value={form.username} onChange={set("username")} disabled={!!editandoId} /></div>
                <div><label style={label}>Nombre</label><input style={input} value={form.first_name} onChange={set("first_name")} /></div>
                <div><label style={label}>Apellido</label><input style={input} value={form.last_name} onChange={set("last_name")} /></div>
                <div><label style={label}>Correo</label><input style={input} type="email" value={form.email} onChange={set("email")} /></div>
                <div><label style={label}>Teléfono</label><input style={input} value={form.telefono} onChange={set("telefono")} /></div>
                <div><label style={label}>Cédula (C.C.)</label><input style={input} value={form.cedula} onChange={set("cedula")} placeholder="Sin puntos" /></div>
                <div><label style={label}>Tarjeta profesional (T.P.)</label><input style={input} value={form.tarjeta_profesional} onChange={set("tarjeta_profesional")} placeholder="Para firmar demandas y contestaciones" /></div>
                <div>
                  <label style={label}>Rol</label>
                  <select style={input} value={form.rol} onChange={set("rol")}>
                    {ROLES.map(([v, t]) => <option key={v} value={v}>{t}</option>)}
                  </select>
                </div>
                <div>
                  <label style={label}>{editandoId ? "Nueva contraseña temporal (opcional)" : "Contraseña temporal"}</label>
                  <div style={{ display: "flex", gap: "6px" }}>
                    <input style={input} type="text" autoComplete="off" value={form.password} onChange={set("password")} />
                    <button type="button" style={btn("#3b6ea5")} onClick={() => setForm({ ...form, password: generarClave() })}>Generar</button>
                  </div>
                </div>
              </div>
              <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px", marginTop: "20px" }}>
                <button type="button" style={btn("#7a8699")} onClick={() => setForm(null)}>Cancelar</button>
                <button type="submit" disabled={guardando} style={btn("#0a1a2b")}>{guardando ? "Guardando..." : "Guardar"}</button>
              </div>
            </form>
          </div>
        )}
      </div>
    </Layout>
  );
}
