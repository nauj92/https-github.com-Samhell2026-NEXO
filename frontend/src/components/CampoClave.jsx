import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";

// Campo de contraseña con el ojo para mostrarla u ocultarla.
// Recibe las mismas propiedades que un <input> (value, onChange, autoComplete, style...).
export default function CampoClave({ style, ...props }) {
  const [visible, setVisible] = useState(false);
  return (
    <div style={{ position: "relative" }}>
      <input {...props} type={visible ? "text" : "password"} style={{ ...style, paddingRight: "42px" }} />
      <button
        type="button"
        onClick={() => setVisible((v) => !v)}
        title={visible ? "Ocultar contraseña" : "Mostrar contraseña"}
        aria-label={visible ? "Ocultar contraseña" : "Mostrar contraseña"}
        style={{ position: "absolute", right: "8px", top: "50%", transform: "translateY(-50%)", background: "none", border: "none", padding: "4px", cursor: "pointer", color: "#8899b4", display: "flex" }}
      >
        {visible ? <EyeOff size={18} /> : <Eye size={18} />}
      </button>
    </div>
  );
}
