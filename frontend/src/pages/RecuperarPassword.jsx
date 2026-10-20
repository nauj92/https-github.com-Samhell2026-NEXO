import { useState } from "react";
import { Link } from "react-router-dom";
import api from "../api";
import { mensajeError } from "../utils/errores";
import AuthLayout, { Aviso, estiloInput, estiloBoton } from "../components/AuthLayout";

export default function RecuperarPassword() {
  const [email, setEmail] = useState("");
  const [msg, setMsg] = useState(null);
  const [enviando, setEnviando] = useState(false);

  const enviar = async (e) => {
    e.preventDefault();
    setMsg(null);
    if (!/^\S+@\S+\.\S+$/.test(email.trim())) {
      setMsg({ tipo: "error", texto: "Ingrese un correo válido." });
      return;
    }
    setEnviando(true);
    try {
      const r = await api.post("/password-reset/", { email: email.trim() });
      setMsg({ tipo: "ok", texto: r.data.detail });
    } catch (err) {
      setMsg({ tipo: "error", texto: mensajeError(err) });
    } finally {
      setEnviando(false);
    }
  };

  return (
    <AuthLayout titulo="Recuperar contraseña">
      <form onSubmit={enviar}>
        {msg && <Aviso tipo={msg.tipo}>{msg.texto}</Aviso>}
        <label style={{ fontSize: "13px", fontWeight: 600 }}>Correo registrado</label>
        <input style={{ ...estiloInput, marginTop: "6px" }} type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        <button type="submit" disabled={enviando} style={{ ...estiloBoton, opacity: enviando ? 0.7 : 1 }}>
          {enviando ? "Enviando..." : "Enviar enlace"}
        </button>
        <p style={{ textAlign: "center", marginTop: "16px", fontSize: "13px" }}>
          <Link to="/login" style={{ color: "#4a5a70" }}>Volver al inicio de sesión</Link>
        </p>
      </form>
    </AuthLayout>
  );
}
