import { useEffect, useState } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import {
  Scale, LogOut, Gavel, Calculator, Eye, FileText, ChevronDown, ChevronRight, Briefcase, Bell,
  FileSignature, Send, Users, CalendarDays,
} from "lucide-react";
import api from "../api";

// Menú con grupos desplegables (pueden anidarse). Un elemento sin `children` es un enlace directo.
const menu = [
  {
    id: "liquidacion", label: "Liquidación", Icon: Calculator,
    children: [
      { to: "/liquidacion/laboral", label: "Laboral", Icon: Gavel },
      { to: "/liquidacion/credito", label: "Créditos", Icon: Gavel },
      { to: "/liquidacion/alimentos", label: "Alimentos", Icon: Gavel },
      { to: "/liquidacion/cuotas", label: "Cuotas de administración", Icon: Gavel },
    ],
  },
  { to: "/vigilancia", label: "Vigilancia judicial", Icon: Eye },
  {
    id: "administracion", label: "Administración judicial", Icon: Briefcase,
    children: [
      {
        id: "gestion-demanda", label: "Gestión de demanda", Icon: FileText,
        children: [
          { to: "/demandas", label: "A1 · Elaboración de demanda", Icon: FileText },
          { to: "/contestaciones", label: "B1 · Contestación de demanda", Icon: FileSignature },
        ],
      },
      { to: "/citaciones", label: "Citación de demanda", Icon: Send },
      { to: "/abogados", label: "Abogados", Icon: Users },
      { to: "/audiencias", label: "Audiencias y diligencias judiciales", Icon: CalendarDays },
    ],
  },
];

// ¿Alguna pantalla de este grupo está activa?
const contiene = (item, ruta) =>
  item.to ? ruta.startsWith(item.to) : item.children.some((h) => contiene(h, ruta));

// ids de todos los grupos (para abrir los ancestros de la pantalla actual)
const idsActivos = (items, ruta) =>
  items.flatMap((m) => (m.children && contiene(m, ruta) ? [m.id, ...idsActivos(m.children, ruta)] : []));

const CLAVE_MENU = "menu_abiertos";

function leerAbiertos() {
  try {
    return JSON.parse(localStorage.getItem(CLAVE_MENU)) || {};
  } catch {
    return {};
  }
}

const rolLabels = {
  administrador: "Administrador",
  socio_director: "Socio Director",
  abogado: "Abogado",
  secretario_juridico: "Secretario Jurídico",
};

export default function Sidebar() {
  const navigate = useNavigate();
  const [perfil, setPerfil] = useState(null);
  const location = useLocation();
  const [abiertos, setAbiertos] = useState(leerAbiertos);

  useEffect(() => {
    api.get("/perfil/").then((response) => setPerfil(response.data)).catch(() => {});
  }, []);

  const [sinLeer, setSinLeer] = useState(0);

  // Si se navega a una pantalla que está dentro de un grupo, ese grupo (y sus padres) se abren solos
  useEffect(() => {
    const ids = idsActivos(menu, location.pathname);
    if (ids.length) setAbiertos((prev) => (ids.every((i) => prev[i]) ? prev : { ...prev, ...Object.fromEntries(ids.map((i) => [i, true])) }));
  }, [location.pathname]);

  // Contador de notificaciones sin leer (se refresca al cambiar de pantalla)
  useEffect(() => {
    api.get("/notificaciones/").then((r) => setSinLeer(r.data.filter((n) => !n.leida).length)).catch(() => {});
  }, [location.pathname]);

  const alternar = (id) => {
    setAbiertos((prev) => {
      const nuevo = { ...prev, [id]: !prev[id] };
      try {
        localStorage.setItem(CLAVE_MENU, JSON.stringify(nuevo));
      } catch {
        /* sin almacenamiento: el menú funciona igual */
      }
      return nuevo;
    });
  };

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
        {menu.map((item) => (
          <ElementoMenu key={item.id || item.to} item={item} nivel={0} abiertos={abiertos} alternar={alternar} ruta={location.pathname} />
        ))}
      </nav>

      <NavLink
        to="/notificaciones"
        style={({ isActive }) => ({
          display: "flex", alignItems: "center", gap: "12px", padding: "10px 16px", borderRadius: "10px", marginBottom: "8px",
          textDecoration: "none", fontSize: "14px", color: isActive ? "white" : "#8899b4", background: isActive ? "#1f3b57" : "transparent",
        })}
      >
        <Bell size={18} />
        <span style={{ flex: 1 }}>Notificaciones</span>
        {sinLeer > 0 && (
          <span style={{ background: "#c73a3a", color: "white", borderRadius: "30px", fontSize: "11px", fontWeight: 700, padding: "2px 8px" }}>{sinLeer}</span>
        )}
      </NavLink>

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

function ElementoMenu({ item, nivel, abiertos, alternar, ruta }) {
  if (!item.children) return <EnlaceMenu {...item} sub={nivel > 0} />;
  const abierto = !!abiertos[item.id];
  const activo = contiene(item, ruta);
  return (
    <div style={{ marginBottom: "4px" }}>
      <button
        type="button"
        onClick={() => alternar(item.id)}
        aria-expanded={abierto}
        style={{
          width: "100%", display: "flex", alignItems: "center", gap: "12px", padding: nivel ? "9px 12px" : "12px 16px",
          borderRadius: "10px", border: "none", cursor: "pointer", fontSize: nivel ? "14px" : "inherit", fontFamily: "inherit",
          fontWeight: 500, textAlign: "left", background: "transparent", color: activo ? "white" : "#8899b4",
        }}
      >
        {nivel === 0 && <item.Icon size={18} />}
        <span style={{ flex: 1 }}>{item.label}</span>
        {abierto ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
      </button>
      {abierto && (
        <div style={{ marginLeft: "18px", paddingLeft: "8px", borderLeft: "1px solid #1e354b" }}>
          {item.children.map((h) => (
            <ElementoMenu key={h.id || h.to} item={h} nivel={nivel + 1} abiertos={abiertos} alternar={alternar} ruta={ruta} />
          ))}
        </div>
      )}
    </div>
  );
}

function EnlaceMenu({ to, label, Icon, sub }) {
  return (
    <NavLink
      to={to}
      style={({ isActive }) => ({
        display: "flex",
        alignItems: "center",
        gap: "12px",
        padding: sub ? "9px 12px" : "12px 16px",
        borderRadius: "10px",
        marginBottom: "4px",
        textDecoration: "none",
        fontSize: sub ? "14px" : "inherit",
        color: isActive ? "white" : "#8899b4",
        background: isActive ? "#1f3b57" : "transparent",
        fontWeight: 500,
      })}
    >
      {!sub && <Icon size={18} />}
      <span>{label}</span>
    </NavLink>
  );
}
