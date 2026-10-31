import { useState } from "react";
import { Scale } from "lucide-react";

const imagenesFondo = [
  "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?q=80&w=1920",
  "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?q=80&w=1920",
  "https://images.unsplash.com/photo-1436450412740-6b988f486c6b?q=80&w=1920",
];

export default function AuthLayout({ titulo, children, ancho = 380 }) {
  const [imagenFondo] = useState(imagenesFondo[Math.floor(Math.random() * imagenesFondo.length)]);
  return (
    <div
      style={{
        display: "flex",
        minHeight: "100vh",
        alignItems: "center",
        justifyContent: "center",
        position: "relative",
        backgroundColor: "#0a1a2b",
        backgroundImage: `url(${imagenFondo})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
        padding: "16px",
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "linear-gradient(135deg, rgba(10,26,43,0.85), rgba(10,26,43,0.6))",
        }}
      />
      <div
        style={{
          position: "relative",
          zIndex: 1,
          background: "white",
          padding: "40px",
          borderRadius: "16px",
          width: "100%",
          maxWidth: `${ancho}px`,
          boxShadow: "0 20px 60px rgba(0,0,0,0.4)",
        }}
      >
        <h2 style={{ marginBottom: "8px", color: "#0a1a2b", display: "flex", alignItems: "center", gap: "10px" }}>
          <Scale size={26} color="#d4a743" /> Lex·ERP
        </h2>
        <h3 style={{ marginBottom: "20px", color: "#4a5a70", fontWeight: 500, fontSize: "15px" }}>{titulo}</h3>
        {children}
      </div>
    </div>
  );
}

export const estiloInput = {
  width: "100%",
  padding: "10px 12px",
  border: "2px solid #e5e9ef",
  borderRadius: "10px",
  fontSize: "14px",
  marginBottom: "14px",
  boxSizing: "border-box",
};

export const estiloBoton = {
  width: "100%",
  padding: "12px",
  background: "#0a1a2b",
  color: "white",
  border: "none",
  borderRadius: "10px",
  cursor: "pointer",
  fontWeight: 600,
  fontSize: "14px",
};

export function Aviso({ tipo, children }) {
  const ok = tipo === "ok";
  return (
    <p
      style={{
        color: ok ? "#1d6b3a" : "#c73a3a",
        background: ok ? "#e6f6ec" : "#fde8e8",
        fontSize: "13px",
        padding: "8px 12px",
        borderRadius: "8px",
        marginBottom: "16px",
        whiteSpace: "pre-line",
      }}
    >
      {children}
    </p>
  );
}
