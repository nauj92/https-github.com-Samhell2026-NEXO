import { useEffect, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { LayoutDashboard, FolderOpen, Scale, Users, Wallet, Flag, LogOut, UserCog } from "lucide-react";
import api from "../api";

const navItems = [
  { to: "/dashboard", label: "Panel", Icon: LayoutDashboard },
  { to: "/expedientes", label: "Expedientes", Icon: FolderOpen },
  { to: "/audiencias", label: "Audiencias", Icon: Scale },
  { to: "/clientes", label: "Clientes", Icon: Users },
  { to: "/facturacion", label: "Facturación", Icon: Wallet },
  { to: "/reportes", label: "Reportes", Icon: Flag },
];

const rolLabels = {
  administrador: "Administrador",
  socio_director: "Socio Director",
  abogado: "Abogado",
  secretario_juridico: "Secretario Jurídico",
};

export default function Sidebar() {
  const navigate = useNavigate();
  const [perfil, setPerfil] = useState(null);

  useEffect(() => {
    api.get("/perfil/").then((response) => setPerfil(response.data)).catch(() => {});
  }, []);

  const items = perfil?.es_directivo
    ? [...navItems, { to: "/usuarios", label: "Usuarios", Icon: UserCog }]
    : navItems;

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    navigate("/login");
  };

  const nombreCompleto = perfil
    ? `${perfil.first_name || ""} ${perfil.last_name || ""}`.trim() || perfil.username
    : "";

  const iniciales = nombreCompleto
    ? nombreCompleto
        .split(" ")
        .slice(0, 2)
        .map((p) => p[0])
        .join("")
        .toUpperCase()
    : "";

  return (
    <aside
      style={{
        width: "260px",
        background: "#0a1a2b",
        color: "#b0c4de",
        display: "flex",
        flexDirection: "column",
        padding: "24px 16px",
        minHeight: "100vh",
      }}
    >
      <div
        style={{
          fontSize: "20px",
          fontWeight: "bold",
          color: "white",
          marginBottom: "32px",
          paddingLeft: "8px",
          display: "flex",
          alignItems: "center",
          gap: "10px",
        }}
      >
        <Scale size={24} color="#d4a743" />
        <span>ERP OPERADOR JUDICIAL</span>
      </div>

      <nav style={{ flex: 1 }}>
        {items.map(({ to, label, Icon }) => (
          <NavLink
            key={to}
            to={to}
            style={({ isActive }) => ({
              display: "flex",
              alignItems: "center",
              gap: "12px",
              padding: "12px 16px",
              borderRadius: "10px",
              marginBottom: "4px",
              textDecoration: "none",
              color: isActive ? "white" : "#8899b4",
              background: isActive ? "#1f3b57" : "transparent",
              fontWeight: 500,
            })}
          >
            <Icon size={18} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {perfil && (
        <div
          onClick={() => navigate("/configuracion")}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            padding: "12px",
            borderTop: "1px solid #1e354b",
            marginBottom: "12px",
            cursor: "pointer",
          }}
        >
          <div
            style={{
              width: "40px",
              height: "40px",
              borderRadius: "50%",
              background: "#d4a743",
              color: "#0a1a2b",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: "bold",
              flexShrink: 0,
            }}
          >
            {iniciales}
          </div>
          <div style={{ overflow: "hidden" }}>
            <div style={{ color: "white", fontWeight: 600, fontSize: "14px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {nombreCompleto}
            </div>
            <div style={{ fontSize: "12px", color: "#8899b4" }}>
              {rolLabels[perfil.rol] || perfil.rol}
            </div>
          </div>
        </div>
      )}

      <button
        onClick={handleLogout}
        style={{
          background: "transparent",
          border: "1px solid #1e354b",
          color: "#b0c4de",
          padding: "10px",
          borderRadius: "8px",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "8px",
        }}
      >
        <LogOut size={16} />
        Cerrar sesión
      </button>
    </aside>
  );
}