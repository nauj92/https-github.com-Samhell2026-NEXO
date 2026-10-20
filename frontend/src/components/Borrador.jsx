import { useState } from "react";
import api from "../api";
import { mensajeError } from "../utils/errores";
import { inputStyle, botonSecundario, mensajeErrorEstilo } from "./ui";

// Editor de borradores: genera el texto desde la plantilla del servidor, lo deja editar y lo guarda.
// `ruta` es, por ejemplo, "/demandas/12" (sin barra final).
export default function Borrador({ ruta, inicial, nombreArchivo, onGuardado }) {
  const [texto, setTexto] = useState(inicial || "");
  const [guardado, setGuardado] = useState(inicial || "");
  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState("");
  const [ocupado, setOcupado] = useState(false);

  const generar = async () => {
    setError("");
    setMensaje("");
    if (texto.trim() && texto !== guardado && !window.confirm("Hay cambios sin guardar. ¿Reemplazarlos por un borrador nuevo?")) return;
    if (texto.trim() && texto === guardado && !window.confirm("Se reemplazará el borrador actual por uno nuevo. ¿Continuar?")) return;
    try {
      const r = await api.get(`${ruta}/generar-borrador/`);
      setTexto(r.data.borrador);
      setMensaje("Borrador generado con los datos actuales. Revíselo, edítelo y guárdelo.");
    } catch (err) {
      setError(mensajeError(err, "No se pudo generar el borrador."));
    }
  };

  const guardar = async () => {
    setError("");
    setMensaje("");
    setOcupado(true);
    try {
      await api.patch(`${ruta}/`, { borrador: texto });
      setGuardado(texto);
      setMensaje("✅ Borrador guardado.");
      if (onGuardado) onGuardado();
    } catch (err) {
      setError(mensajeError(err, "No se pudo guardar el borrador."));
    } finally {
      setOcupado(false);
    }
  };

  const descargar = () => {
    const blob = new Blob([texto], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${nombreArchivo || "borrador"}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ marginTop: "18px", borderTop: "1px solid #eef2f6", paddingTop: "14px" }}>
      <div style={{ fontSize: "11px", color: "#6b7f96", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: "6px" }}>Borrador del escrito</div>
      <p style={{ fontSize: "12px", color: "#6b7f96", margin: "0 0 8px" }}>
        Es un punto de partida creado desde una plantilla: debe ser revisado y completado por el abogado antes de presentarse.
      </p>
      {error && <p style={mensajeErrorEstilo}>{error}</p>}
      {mensaje && <p style={{ fontSize: "13px", color: "#1d6b3a" }}>{mensaje}</p>}
      <textarea rows={12} value={texto} onChange={(e) => setTexto(e.target.value)} placeholder="Aún no hay borrador. Use “Generar borrador”." style={{ ...inputStyle, fontFamily: "monospace", fontSize: "13px" }} />
      <div style={{ display: "flex", gap: "8px", marginTop: "8px", flexWrap: "wrap" }}>
        <button type="button" onClick={generar} style={botonSecundario}>Generar borrador</button>
        <button type="button" onClick={guardar} disabled={ocupado || texto === guardado} style={{ ...botonSecundario, background: "#0a1a2b", color: "white" }}>
          {ocupado ? "Guardando..." : "Guardar borrador"}
        </button>
        <button type="button" onClick={descargar} disabled={!texto.trim()} style={botonSecundario}>Descargar .txt</button>
      </div>
    </div>
  );
}
