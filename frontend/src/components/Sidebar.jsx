import { useEffect, useState } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import {
  Scale, LogOut, Gavel, Calculator, Eye, FileText, ChevronDown, ChevronRight, Briefcase, Bell,
  FileSignature, Send, Users, CalendarDays, Contact, LayoutDashboard, ChevronsLeft, ChevronsRight,
} from "lucide-react";
import api from "../api";

// Menú con grupos desplegables (pueden anidarse). Un elemento sin `children` es un enlace directo.
const menu = [
  { to: "/dashboard", label: "Dashboard", Icon: LayoutDashboard },
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
      { to: "/clientes", label: "Clientes", Icon: Contact },
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
const CLAVE_COMPACTO = "menu_colapsado";

// Paleta del menú: azul institucional más claro, con dorado como acento.
const COLOR = {
  fondo: "linear-gradient(180deg, #1d3f66 0%, #25507d 100%)",
  texto: "#dbe6f2",
  apagado: "#b4c6da",
  activo: "#3b6ea5",
  hover: "#2d5b8d",
  borde: "#4a77a8",
  acento: "#d4a743",
};

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

  // Menú compacto (solo iconos): se recuerda en el navegador y solo aplica en pantallas grandes.
  const [preferCompacto, setPreferCompacto] = useState(() => {
    try {
      return localStorage.getItem(CLAVE_COMPACTO) === "1";
    } catch {
      return false;
    }
  });
  const [esMovil, setEsMovil] = useState(() => window.matchMedia("(max-width: 1100px)").matches);
  useEffect(() => {
    const mq = window.matchMedia("(max-width: 1100px)");
    const f = () => setEsMovil(mq.matches);
    mq.addEventListener("change", f);
    return () => mq.removeEventListener("change", f);
  }, []);
  const compacto = preferCompacto && !esMovil;
  const cambiarCompacto = (valor) => {
    setPreferCompacto(valor);
    try {
      localStorage.setItem(CLAVE_COMPACTO, valor ? "1" : "0");
    } catch {
      /* sin almacenamiento */
    }
  };

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
    try {
      localStorage.removeItem(CLAVE_MENU);
    } catch {
      /* sin almacenamiento */
    }
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
        width: compacto ? "76px" : "260px",
        background: COLOR.fondo,
        color: COLOR.texto,
        display: "flex",
        flexDirection: "column",
        padding: compacto ? "24px 10px" : "24px 16px",
        minHeight: "100vh",
        transition: "width 0.2s ease",
        overflowX: "hidden",
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
        <Scale size={24} color={COLOR.acento} style={{ flexShrink: 0 }} />
        {!compacto && <span style={{ flex: 1 }}>ERP OPERADOR JUDICIAL</span>}
      </div>

      {!esMovil && (
        <button
          type="button"
          onClick={() => cambiarCompacto(!compacto)}
          title={compacto ? "Desplegar menú" : "Plegar menú"}
          aria-label={compacto ? "Desplegar menú" : "Plegar menú"}
          style={{ alignSelf: compacto ? "center" : "flex-end", background: "rgba(255,255,255,0.12)", border: "none", color: "white", borderRadius: "8px", padding: "6px", cursor: "pointer", display: "flex", marginBottom: "14px" }}
        >
          {compacto ? <ChevronsRight size={18} /> : <ChevronsLeft size={18} />}
        </button>
      )}

      <nav style={{ flex: 1 }}>
        {menu.map((item) => (
          <ElementoMenu key={item.id || item.to} item={item} nivel={0} abiertos={abiertos} alternar={alternar} ruta={location.pathname} compacto={compacto} expandir={() => cambiarCompacto(false)} />
        ))}
      </nav>

      <NavLink
        to="/notificaciones"
        style={({ isActive }) => ({
          display: "flex", alignItems: "center", justifyContent: compacto ? "center" : "flex-start", gap: "12px", padding: compacto ? "10px 0" : "10px 16px", borderRadius: "10px", marginBottom: "8px",
          textDecoration: "none", fontSize: "14px", color: isActive ? "white" : COLOR.apagado, background: isActive ? COLOR.activo : "transparent",
          boxShadow: isActive ? `inset 3px 0 0 ${COLOR.acento}` : "none",
        })}
        title="Notificaciones"
      >
        <Bell size={18} />
        {!compacto && <span style={{ flex: 1 }}>Notificaciones</span>}
        {sinLeer > 0 && !compacto && (
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
            padding: compacto ? "12px 0" : "12px",
            justifyContent: compacto ? "center" : "flex-start",
            borderTop: `1px solid ${COLOR.borde}`,
            marginBottom: "12px",
            cursor: "pointer",
          }}
        >
          <div
            style={{
              width: "40px",
              height: "40px",
              borderRadius: "50%",
              background: COLOR.acento,
              color: "#14304f",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: "bold",
              flexShrink: 0,
            }}
          >
            {iniciales}
          </div>
          {!compacto && <div style={{ overflow: "hidden" }}>
            <div style={{ color: "white", fontWeight: 600, fontSize: "14px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {nombreCompleto}
            </div>
            <div style={{ fontSize: "12px", color: COLOR.apagado }}>
              {rolLabels[perfil.rol] || perfil.rol}
            </div>
          </div>}
        </div>
      )}

      <button
        onClick={handleLogout}
        title="Cerrar sesión"
        style={{
          background: "transparent",
          border: `1px solid ${COLOR.borde}`,
          color: COLOR.texto,
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
        {!compacto && "Cerrar sesión"}
      </button>
    </aside>
  );
}

function ElementoMenu({ item, nivel, abiertos, alternar, ruta, compacto, expandir }) {
  if (!item.children) return <EnlaceMenu {...item} sub={nivel > 0} compacto={compacto} />;
  const abierto = !!abiertos[item.id];
  const activo = contiene(item, ruta);
  return (
    <div style={{ marginBottom: "4px" }}>
      <button
        type="button"
        onClick={() => {
          if (compacto) {
            expandir();
            if (!abierto) alternar(item.id);
          } else alternar(item.id);
        }}
        title={item.label}
        aria-expanded={abierto}
        style={{
          width: "100%", display: "flex", alignItems: "center", justifyContent: compacto ? "center" : "flex-start", gap: "12px", padding: compacto ? "12px 0" : nivel ? "9px 12px" : "12px 16px",
          borderRadius: "10px", border: "none", cursor: "pointer", fontSize: nivel ? "14px" : "inherit", fontFamily: "inherit",
          fontWeight: 500, textAlign: "left", background: activo && nivel === 0 ? "rgba(255,255,255,0.10)" : "transparent", color: activo ? "white" : COLOR.apagado,
        }}
      >
        {nivel === 0 && <item.Icon size={18} />}
        {!compacto && <span style={{ flex: 1, textAlign: "left" }}>{item.label}</span>}
        {!compacto && (abierto ? <ChevronDown size={16} /> : <ChevronRight size={16} />)}
      </button>
      {abierto && !compacto && (
        <div style={{ marginLeft: "18px", paddingLeft: "8px", borderLeft: `1px solid ${COLOR.borde}` }}>
          {item.children.map((h) => (
            <ElementoMenu key={h.id || h.to} item={h} nivel={nivel + 1} abiertos={abiertos} alternar={alternar} ruta={ruta} compacto={compacto} expandir={expandir} />
          ))}
        </div>
      )}
    </div>
  );
}

function EnlaceMenu({ to, label, Icon, sub, compacto }) {
  return (
    <NavLink
      to={to}
      style={({ isActive }) => ({
        display: "flex",
        alignItems: "center",
        justifyContent: compacto ? "center" : "flex-start",
        gap: "12px",
        padding: compacto ? "12px 0" : sub ? "9px 12px" : "12px 16px",
        borderRadius: "10px",
        marginBottom: "4px",
        textDecoration: "none",
        fontSize: sub ? "14px" : "inherit",
        color: isActive ? "white" : COLOR.apagado,
        background: isActive ? COLOR.activo : "transparent",
        boxShadow: isActive ? `inset 3px 0 0 ${COLOR.acento}` : "none",
        fontWeight: 500,
      })}
      title={label}
    >
      {!sub && <Icon size={18} />}
      {!compacto && <span>{label}</span>}
    </NavLink>
  );
}
