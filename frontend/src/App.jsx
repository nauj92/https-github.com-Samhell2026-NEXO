import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Expedientes from "./pages/Expedientes";
import Audiencias from "./pages/Audiencias";
import Configuracion from "./pages/Configuracion";
import Abogados from "./pages/Abogados";
import Demandas from "./pages/Demandas";
import Contestaciones from "./pages/Contestaciones";
import Citaciones from "./pages/Citaciones";
import Vigilancia from "./pages/Vigilancia";
import Liquidacion from "./pages/Liquidacion";
import Notificaciones from "./pages/Notificaciones";
import RecuperarPassword from "./pages/RecuperarPassword";
import RestablecerPassword from "./pages/RestablecerPassword";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" />} />
        <Route path="/login" element={<Login />} />
        <Route path="/recuperar" element={<RecuperarPassword />} />
        <Route path="/restablecer/:uid/:token" element={<RestablecerPassword />} />

        {/* Liquidación */}
        <Route path="/liquidacion" element={<Navigate to="/liquidacion/laboral" replace />} />
        <Route path="/liquidacion/:tipo" element={<Liquidacion />} />

        {/* Vigilancia judicial */}
        <Route path="/vigilancia" element={<Vigilancia />} />

        {/* Administración judicial */}
        <Route path="/demandas" element={<Demandas />} />
        <Route path="/contestaciones" element={<Contestaciones />} />
        <Route path="/citaciones" element={<Citaciones />} />
        <Route path="/abogados" element={<Abogados />} />
        <Route path="/audiencias" element={<Audiencias />} />

        {/* Fuera del menú: se llega desde los módulos, la tarjeta de perfil o la campana */}
        <Route path="/expedientes" element={<Expedientes />} />
        <Route path="/notificaciones" element={<Notificaciones />} />
        <Route path="/configuracion" element={<Configuracion />} />

        {/* Rutas de pantallas retiradas del menú */}
        <Route path="/usuarios" element={<Navigate to="/abogados" replace />} />
        <Route path="*" element={<Navigate to="/liquidacion/laboral" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
