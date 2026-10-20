import { useEffect, useState } from "react";
import api from "../api";
import { mensajeError } from "../utils/errores";
import Layout from "../components/Layout";
import { Settings, User, Lock, Eye, EyeOff } from "lucide-react";

export default function Configuracion() {
  const [perfil, setPerfil] = useState(null);
  const [guardandoPerfil, setGuardandoPerfil] = useState(false);
  const [mensajePerfil, setMensajePerfil] = useState("");

  const [passwordForm, setPasswordForm] = useState({ password_actual: "", password_nueva: "", password_confirmar: "" });
  const [mostrarActual, setMostrarActual] = useState(false);
  const [mostrarNueva, setMostrarNueva] = useState(false);
  const [mostrarConfirmar, setMostrarConfirmar] = useState(false);
  const [guardandoPassword, setGuardandoPassword] = useState(false);
  const [mensajePassword, setMensajePassword] = useState("");

  useEffect(() => {
    api.get("/perfil/").then((response) => setPerfil(response.data)).catch(() => {});
  }, []);

  const handleChangePerfil = (e) => {
    setPerfil({ ...perfil, [e.target.name]: e.target.value });
  };

  const handleGuardarPerfil = async (e) => {
    e.preventDefault();
    setMensajePerfil("");
    setGuardandoPerfil(true);
    try {
      const response = await api.patch("/perfil/", {
        first_name: perfil.first_name,
        last_name: perfil.last_name,
        email: perfil.email,
        telefono: perfil.telefono,
      });
      setPerfil(response.data);
      setMensajePerfil("✅ Perfil actualizado correctamente.");
    } catch (err) {
      setMensajePerfil(`❌ ${mensajeError(err, "No se pudo actualizar el perfil.")}`);
    } finally {
      setGuardandoPerfil(false);
    }
  };

  const handleChangePassword = (e) => {
    setPasswordForm({ ...passwordForm, [e.target.name]: e.target.value });
  };

  const handleGuardarPassword = async (e) => {
    e.preventDefault();
    setMensajePassword("");

    if (passwordForm.password_nueva !== passwordForm.password_confirmar) {
      setMensajePassword("❌ Las contraseñas nuevas no coinciden.");
      return;
    }

    setGuardandoPassword(true);
    try {
      await api.post("/perfil/cambiar-password/", {
        password_actual: passwordForm.password_actual,
        password_nueva: passwordForm.password_nueva,
      });
      setMensajePassword("✅ Contraseña actualizada correctamente.");
      setPasswordForm({ password_actual: "", password_nueva: "", password_confirmar: "" });
    } catch (err) {
      setMensajePassword(`❌ ${mensajeError(err, "No se pudo cambiar la contraseña.")}`);
    } finally {
      setGuardandoPassword(false);
    }
  };

  return (
    <Layout>
      <div style={{ minHeight: "100vh", background: "#f4f7fb", fontFamily: "sans-serif" }}>
        <header
          style={{
            background: "white",
            padding: "16px 32px",
            fontSize: "20px",
            fontWeight: "bold",
            borderBottom: "1px solid #e9edf2",
            display: "flex",
            alignItems: "center",
            gap: "10px",
          }}
        >
          <Settings size={22} />
          Configuración
        </header>

        <main style={{ padding: "32px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", maxWidth: "900px" }}>
          {/* Editar perfil */}
          <div style={{ background: "white", borderRadius: "16px", padding: "24px", border: "1px solid #eef2f6" }}>
            <h3 style={{ marginBottom: "16px", display: "flex", alignItems: "center", gap: "8px" }}>
              <User size={18} />
              Mi Perfil
            </h3>
            {!perfil && <p>Cargando...</p>}
            {perfil && (
              <form onSubmit={handleGuardarPerfil}>
                <Campo label="Usuario">
                  <input value={perfil.username} disabled style={{ ...inputStyle, background: "#f4f7fb" }} />
                </Campo>
                <Campo label="Rol">
                  <input value={perfil.rol} disabled style={{ ...inputStyle, background: "#f4f7fb" }} />
                </Campo>
                <Campo label="Nombre">
                  <input name="first_name" value={perfil.first_name || ""} onChange={handleChangePerfil} style={inputStyle} />
                </Campo>
                <Campo label="Apellidos">
                  <input name="last_name" value={perfil.last_name || ""} onChange={handleChangePerfil} style={inputStyle} />
                </Campo>
                <Campo label="Email">
                  <input type="email" name="email" value={perfil.email || ""} onChange={handleChangePerfil} style={inputStyle} />
                </Campo>
                <Campo label="Teléfono">
                  <input name="telefono" value={perfil.telefono || ""} onChange={handleChangePerfil} style={inputStyle} />
                </Campo>

                {mensajePerfil && <p style={{ fontSize: "13px", whiteSpace: "pre-line" }}>{mensajePerfil}</p>}

                <button
                  type="submit"
                  disabled={guardandoPerfil}
                  style={{ padding: "10px 20px", borderRadius: "8px", border: "none", background: "#0a1a2b", color: "white", cursor: "pointer", marginTop: "8px" }}
                >
                  {guardandoPerfil ? "Guardando..." : "Guardar cambios"}
                </button>
              </form>
            )}
          </div>

          {/* Cambiar contraseña */}
          <div style={{ background: "white", borderRadius: "16px", padding: "24px", border: "1px solid #eef2f6" }}>
            <h3 style={{ marginBottom: "16px", display: "flex", alignItems: "center", gap: "8px" }}>
              <Lock size={18} />
              Cambiar Contraseña
            </h3>
            <form onSubmit={handleGuardarPassword}>
              <Campo label="Contraseña actual">
                <div style={{ position: "relative" }}>
                  <input
                    type={mostrarActual ? "text" : "password"}
                    name="password_actual"
                    value={passwordForm.password_actual}
                    onChange={handleChangePassword}
                    required
                    style={{ ...inputStyle, paddingRight: "40px" }}
                  />
                  <span
                    onClick={() => setMostrarActual(!mostrarActual)}
                    style={{ position: "absolute", right: "10px", top: "50%", transform: "translateY(-50%)", cursor: "pointer", color: "#8899b4" }}
                  >
                    {mostrarActual ? <EyeOff size={16} /> : <Eye size={16} />}
                  </span>
                </div>
              </Campo>

              <Campo label="Contraseña nueva">
                <div style={{ position: "relative" }}>
                  <input
                    type={mostrarNueva ? "text" : "password"}
                    name="password_nueva"
                    value={passwordForm.password_nueva}
                    onChange={handleChangePassword}
                    required
                    style={{ ...inputStyle, paddingRight: "40px" }}
                  />
                  <span
                    onClick={() => setMostrarNueva(!mostrarNueva)}
                    style={{ position: "absolute", right: "10px", top: "50%", transform: "translateY(-50%)", cursor: "pointer", color: "#8899b4" }}
                  >
                    {mostrarNueva ? <EyeOff size={16} /> : <Eye size={16} />}
                  </span>
                </div>
              </Campo>

              <Campo label="Confirmar contraseña nueva">
                <div style={{ position: "relative" }}>
                  <input
                    type={mostrarConfirmar ? "text" : "password"}
                    name="password_confirmar"
                    value={passwordForm.password_confirmar}
                    onChange={handleChangePassword}
                    required
                    style={{ ...inputStyle, paddingRight: "40px" }}
                  />
                  <span
                    onClick={() => setMostrarConfirmar(!mostrarConfirmar)}
                    style={{ position: "absolute", right: "10px", top: "50%", transform: "translateY(-50%)", cursor: "pointer", color: "#8899b4" }}
                  >
                    {mostrarConfirmar ? <EyeOff size={16} /> : <Eye size={16} />}
                  </span>
                </div>
              </Campo>

              {mensajePassword && <p style={{ fontSize: "13px", whiteSpace: "pre-line" }}>{mensajePassword}</p>}

              <button
                type="submit"
                disabled={guardandoPassword}
                style={{ padding: "10px 20px", borderRadius: "8px", border: "none", background: "#0a1a2b", color: "white", cursor: "pointer", marginTop: "8px" }}
              >
                {guardandoPassword ? "Guardando..." : "Cambiar contraseña"}
              </button>
            </form>
          </div>
        </main>
      </div>
    </Layout>
  );
}

function Campo({ label, children }) {
  return (
    <div style={{ marginBottom: "14px" }}>
      <label style={{ fontSize: "13px", color: "#6b7f96", display: "block", marginBottom: "4px" }}>{label}</label>
      {children}
    </div>
  );
}

const inputStyle = {
  width: "100%",
  padding: "8px 10px",
  borderRadius: "8px",
  border: "1px solid #d0d9e3",
  fontSize: "14px",
  boxSizing: "border-box",
};