import { useEffect, useState } from "react";
import { Users } from "lucide-react";
import api from "../api";
import Layout from "../components/Layout";
import { mensajeError } from "../utils/errores";

const ROLES = [
  ["administrador", "Administrador"],
  ["socio_director", "Socio Director"],
  ["abogado", "Abogado"],
  ["secretario_juridico", "Secretario Jurídico"],
];

const vacio = { username: "", first_name: "", last_name: "", email: "", telefono: "", rol: "abogado", password: "" };

const input = { width: "100%", padding: "8px 10px", border: "1px solid #d5dbe5", borderRadius: "8px", fontSize: "14px", boxSizing: "border-box" };
const label = { fontSize: "12px", fontWeight: 600, color: "#4a5a70", display: "block", marginBottom: "4px" };
const btn = (bg) => ({ background: bg, color: "white", border: "none", borderRadius: "8px", padding: "8px 14px", cursor: "pointer", fontWeight: 600, fontSize: "13px" });

export default function Usuarios() {
  const [usuarios, setUsuarios] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");
  const [form, setForm] = useState(null); // null = cerrado
  const [editandoId, setEditandoId] = useState(null);
  const [formError, setFormError] = useState("");
  const [guardando, setGuardando] = useState(false);

  const cargar = () => {
    setCargando(true);
    api
      .get("/gestion-usuarios/")
      .then((r) => setUsuarios(r.data.results ?? r.data))
      .catch((err) => setError(mensajeError(err, "No se pudieron cargar los usuarios.")))
      .finally(() => setCargando(false));
  };
  useEffect(cargar, []);

  const abrirNuevo = () => { setForm({ ...vacio }); setEditandoId(null); setFormError(""); };
  const abrirEditar = (u) => {
    setForm({ username: u.username, first_name: u.first_name, last_name: u.last_name, email: u.email, telefono: u.telefono || "", rol: u.rol, password: "" });
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
      if (editandoId) await api.patch(`/gestion-usuarios/${editandoId}/`, datos);
      else await api.post("/gestion-usuarios/", datos);
      setForm(null);
      setAviso(editandoId ? "Usuario actualizado." : "Usuario creado.");
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
            <Users size={26} /> Usuarios
          </h1>
          <button style={btn("#0a1a2b")} onClick={abrirNuevo}>+ Nuevo usuario</button>
        </div>

        {error && <p style={{ color: "#c73a3a", background: "#fde8e8", padding: "8px 12px", borderRadius: "8px", whiteSpace: "pre-line" }}>{error}</p>}
        {aviso && <p style={{ color: "#1d6b3a", background: "#e6f6ec", padding: "8px 12px", borderRadius: "8px" }}>{aviso}</p>}

        {cargando ? (
          <p>Cargando...</p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse", background: "white", borderRadius: "12px", overflow: "hidden" }}>
            <thead>
              <tr style={{ background: "#f1f4f9", textAlign: "left", fontSize: "13px" }}>
                {["Usuario", "Nombre", "Correo", "Rol", "Estado", "Acciones"].map((h) => (
                  <th key={h} style={{ padding: "12px" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {usuarios.map((u) => (
                <tr key={u.id} style={{ borderTop: "1px solid #eef1f6", fontSize: "14px" }}>
                  <td style={{ padding: "12px" }}>{u.username}</td>
                  <td style={{ padding: "12px" }}>{u.nombre_completo}</td>
                  <td style={{ padding: "12px" }}>{u.email}</td>
                  <td style={{ padding: "12px" }}>{(ROLES.find((r) => r[0] === u.rol) || [])[1] || u.rol}</td>
                  <td style={{ padding: "12px", color: u.is_active ? "#1d6b3a" : "#c73a3a" }}>{u.is_active ? "Activo" : "Inactivo"}</td>
                  <td style={{ padding: "12px", display: "flex", gap: "6px", flexWrap: "wrap" }}>
                    <button style={btn("#3a6ea5")} onClick={() => abrirEditar(u)}>Editar</button>
                    <button style={btn(u.is_active ? "#c73a3a" : "#2e8b57")} onClick={() => alternarActivo(u)}>
                      {u.is_active ? "Desactivar" : "Activar"}
                    </button>
                    <button style={btn("#7a8699")} onClick={() => desbloquear(u)}>Desbloquear</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {form && (
          <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 50 }}>
            <form onSubmit={guardar} style={{ background: "white", padding: "28px", borderRadius: "14px", width: "420px", maxHeight: "90vh", overflowY: "auto" }}>
              <h3 style={{ marginTop: 0 }}>{editandoId ? "Editar usuario" : "Nuevo usuario"}</h3>
              {formError && <p style={{ color: "#c73a3a", background: "#fde8e8", padding: "8px 12px", borderRadius: "8px", fontSize: "13px", whiteSpace: "pre-line" }}>{formError}</p>}
              <div style={{ display: "grid", gap: "12px" }}>
                <div><label style={label}>Usuario</label><input style={input} value={form.username} onChange={set("username")} disabled={!!editandoId} /></div>
                <div><label style={label}>Nombre</label><input style={input} value={form.first_name} onChange={set("first_name")} /></div>
                <div><label style={label}>Apellido</label><input style={input} value={form.last_name} onChange={set("last_name")} /></div>
                <div><label style={label}>Correo</label><input style={input} type="email" value={form.email} onChange={set("email")} /></div>
                <div><label style={label}>Teléfono</label><input style={input} value={form.telefono} onChange={set("telefono")} /></div>
                <div>
                  <label style={label}>Rol</label>
                  <select style={input} value={form.rol} onChange={set("rol")}>
                    {ROLES.map(([v, t]) => <option key={v} value={v}>{t}</option>)}
                  </select>
                </div>
                <div>
                  <label style={label}>{editandoId ? "Nueva contraseña (opcional)" : "Contraseña"}</label>
                  <input style={input} type="password" value={form.password} onChange={set("password")} />
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
