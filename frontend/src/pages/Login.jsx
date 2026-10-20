import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Scale, User, Lock } from "lucide-react";
import api from "../api";
import { mensajeError } from "../utils/errores";

const imagenesFondo = [
  "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?q=80&w=1920",
  "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?q=80&w=1920",
  "https://images.unsplash.com/photo-1436450412740-6b988f486c6b?q=80&w=1920",
];

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [focoUsuario, setFocoUsuario] = useState(false);
  const [focoPassword, setFocoPassword] = useState(false);
  const navigate = useNavigate();

  const [imagenFondo] = useState(
    imagenesFondo[Math.floor(Math.random() * imagenesFondo.length)]
  );

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!username.trim() || !password) {
      setError("Ingrese su usuario y contraseña.");
      return;
    }
    setEnviando(true);
    try {
      const response = await api.post("/token/", { username, password });
      localStorage.setItem("access_token", response.data.access);
      localStorage.setItem("refresh_token", response.data.refresh);
      navigate("/liquidacion/laboral");
    } catch (err) {
      const st = err.response?.status;
      if (st === 401 || st === 400) setError("Usuario o contraseña incorrectos.");
      else if (st === 403 || st === 429)
        setError("Cuenta bloqueada temporalmente por demasiados intentos fallidos. Espere una hora o pida a un administrador que la desbloquee.");
      else setError(mensajeError(err));
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
        alignItems: "center",
        justifyContent: "center",
        position: "relative",
        backgroundImage: `url(${imagenFondo})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "linear-gradient(135deg, rgba(10,26,43,0.85), rgba(10,26,43,0.6))",
        }}
      />

      <form
        onSubmit={handleSubmit}
        style={{
          position: "relative",
          zIndex: 1,
          background: "white",
          padding: "40px",
          borderRadius: "16px",
          width: "340px",
          boxShadow: "0 20px 60px rgba(0,0,0,0.4)",
        }}
      >
        <h2 style={{ marginBottom: "28px", color: "#0a1a2b", display: "flex", alignItems: "center", gap: "10px" }}>
          <Scale size={26} color="#d4a743" />
          ·ERP
        </h2>

        {error && (
          <p style={{ color: "#c73a3a", fontSize: "13px", background: "#fde8e8", padding: "8px 12px", borderRadius: "8px", marginBottom: "16px" }}>
            {error}
          </p>
        )}

        <div style={{ marginBottom: "18px" }}>
          <label style={{ fontSize: "13px", fontWeight: 600, color: "#1a2c3e", display: "block", marginBottom: "6px" }}>
            Usuario
          </label>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              border: focoUsuario ? "2px solid #0a1a2b" : "2px solid #e5e9ef",
              borderRadius: "10px",
              padding: "10px 14px",
              background: "#f8fafc",
              transition: "border-color 0.15s",
            }}
          >
            <User size={18} color="#8899b4" />
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              onFocus={() => setFocoUsuario(true)}
              onBlur={() => setFocoUsuario(false)}
              style={{
                border: "none",
                background: "transparent",
                outline: "none",
                fontSize: "14px",
                width: "100%",
              }}
            />
          </div>
        </div>

        <div style={{ marginBottom: "24px" }}>
          <label style={{ fontSize: "13px", fontWeight: 600, color: "#1a2c3e", display: "block", marginBottom: "6px" }}>
            Contraseña
          </label>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              border: focoPassword ? "2px solid #0a1a2b" : "2px solid #e5e9ef",
              borderRadius: "10px",
              padding: "10px 14px",
              background: "#f8fafc",
              transition: "border-color 0.15s",
            }}
          >
            <Lock size={18} color="#8899b4" />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onFocus={() => setFocoPassword(true)}
              onBlur={() => setFocoPassword(false)}
              style={{
                border: "none",
                background: "transparent",
                outline: "none",
                fontSize: "14px",
                width: "100%",
              }}
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={enviando}
          style={{
            opacity: enviando ? 0.7 : 1,
            width: "100%",
            padding: "12px",
            background: "#0a1a2b",
            color: "white",
            border: "none",
            borderRadius: "10px",
            cursor: "pointer",
            fontWeight: 600,
            fontSize: "14px",
          }}
        >
          {enviando ? "Ingresando..." : "Ingresar"}
        </button>
        <p style={{ textAlign: "center", marginTop: "16px", fontSize: "13px" }}>
          <Link to="/recuperar" style={{ color: "#4a5a70" }}>¿Olvidó su contraseña?</Link>
        </p>
      </form>
    </div>
  );
}