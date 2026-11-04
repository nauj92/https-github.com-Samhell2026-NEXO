import { useState } from "react";
import { Moon, Sun } from "lucide-react";
import { aplicarTema } from "../utils/tema";

// Botón para pasar de modo diurno a nocturno y al revés.
// `etiqueta` muestra el texto junto al ícono; `estilo` permite adaptarlo a cada lugar.
export default function BotonTema({ etiqueta = false, estilo = {}, className }) {
  const [oscuro, setOscuro] = useState(() => document.documentElement.getAttribute("data-tema") === "oscuro");

  const alternar = () => setOscuro(aplicarTema(oscuro ? "claro" : "oscuro") === "oscuro");
  const texto = oscuro ? "Modo diurno" : "Modo nocturno";

  return (
    <button
      type="button"
      className={className}
      onClick={alternar}
      title={texto}
      aria-label={texto}
      style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", cursor: "pointer", ...estilo }}
    >
      {oscuro ? <Sun size={16} /> : <Moon size={16} />}
      {etiqueta && texto}
    </button>
  );
}
