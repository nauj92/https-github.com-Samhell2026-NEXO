import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { Menu, Scale, X } from "lucide-react";
import Sidebar from "./Sidebar";

// En pantallas grandes el menú está fijo a la izquierda; en celulares y tabletas
// se convierte en un panel que se abre con el botón de la barra superior.
export default function Layout({ children }) {
  const [abierto, setAbierto] = useState(false);
  const { pathname } = useLocation();

  // Al cambiar de pantalla el panel se cierra solo
  useEffect(() => {
    setAbierto(false);
  }, [pathname]);

  return (
    <div className="app-layout">
      <div className="barra-movil">
        <button type="button" className="boton-menu" onClick={() => setAbierto(true)} aria-label="Abrir menú">
          <Menu size={22} />
        </button>
        <Scale size={20} color="#d4a743" />
        <span>ERP OPERADOR JUDICIAL</span>
      </div>

      {abierto && <div className="menu-fondo" onClick={() => setAbierto(false)} />}
      <div className={`menu-lateral${abierto ? " abierto" : ""}`}>
        <button type="button" className="boton-cerrar-menu" onClick={() => setAbierto(false)} aria-label="Cerrar menú">
          <X size={20} />
        </button>
        <Sidebar />
      </div>

      <div className="contenido">{children}</div>
    </div>
  );
}
