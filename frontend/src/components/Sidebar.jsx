import { NavLink, useNavigate } from "react-router-dom";

const navItems = [
  { to: "/dashboard", label: "Panel", icon: "📊" },
  { to: "/expedientes", label: "Expedientes", icon: "📁" },
  { to: "/audiencias", label: "Audiencias", icon: "⚖️" },
  { to: "/clientes", label: "Clientes", icon: "👥" },
  { to: "/facturacion", label: "Facturación", icon: "💰" },
  { to: "/reportes", label: "Reportes", icon: "🚩" },
];

export default function Sidebar() {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    navigate("/login");
  };

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
          fontSize: "22px",
          fontWeight: "bold",
          color: "white",
          marginBottom: "32px",
          paddingLeft: "8px",
        }}
      >
        ⚖️ ERP. OPERADOR JUDICIAL.
      </div>

      <nav style={{ flex: 1 }}>
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
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
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <button
        onClick={handleLogout}
        style={{
          background: "transparent",
          border: "1px solid #1e354b",
          color: "#b0c4de",
          padding: "10px",
          borderRadius: "8px",
          cursor: "pointer",
        }}
      >
        Cerrar sesión
      </button>
    </aside>
  );
}