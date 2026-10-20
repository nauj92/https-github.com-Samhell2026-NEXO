import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import api from "../api";
import { mensajeError } from "../utils/errores";
import AuthLayout, { Aviso, estiloInput, estiloBoton } from "../components/AuthLayout";

export default function RestablecerPassword() {
  const { uid, token } = useParams();
  const [p1, setP1] = useState("");
  const [p2, setP2] = useState("");
  const [msg, setMsg] = useState(null);
  const [listo, setListo] = useState(false);
  const [enviando, setEnviando] = useState(false);

  const enviar = async (e) => {
    e.preventDefault();
    setMsg(null);
    if (p1.length < 8) return setMsg({ tipo: "error", texto: "La contraseña debe tener al menos 8 caracteres." });
    if (p1 !== p2) return setMsg({ tipo: "error", texto: "Las contraseñas no coinciden." });
    setEnviando(true);
    try {
      const r = await api.post("/password-reset/confirmar/", { uid, token, password_nueva: p1 });
      setMsg({ tipo: "ok", texto: r.data.detail });
      setListo(true);
    } catch (err) {
      setMsg({ tipo: "error", texto: mensajeError(err) });
    } finally {
      setEnviando(false);
    }
  };

  return (
    <AuthLayout titulo="Nueva contraseña">
      <form onSubmit={enviar}>
        {msg && <Aviso tipo={msg.tipo}>{msg.texto}</Aviso>}
        {!listo && (
          <>
            <label style={{ fontSize: "13px", fontWeight: 600 }}>Contraseña nueva</label>
            <input style={{ ...estiloInput, marginTop: "6px" }} type="password" value={p1} onChange={(e) => setP1(e.target.value)} />
            <label style={{ fontSize: "13px", fontWeight: 600 }}>Repetir contraseña</label>
            <input style={{ ...estiloInput, marginTop: "6px" }} type="password" value={p2} onChange={(e) => setP2(e.target.value)} />
            <button type="submit" disabled={enviando} style={{ ...estiloBoton, opacity: enviando ? 0.7 : 1 }}>
              {enviando ? "Guardando..." : "Guardar contraseña"}
            </button>
          </>
        )}
        <p style={{ textAlign: "center", marginTop: "16px", fontSize: "13px" }}>
          <Link to="/login" style={{ color: "#4a5a70" }}>Ir al inicio de sesión</Link>
        </p>
      </form>
    </AuthLayout>
  );
}
