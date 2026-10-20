import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Expedientes from "./pages/Expedientes";
import Audiencias from "./pages/Audiencias";
import Clientes from "./pages/Clientes";
import Facturacion from "./pages/Facturacion";
import Reportes from "./pages/Reportes";
import Configuracion from "./pages/Configuracion";
import Usuarios from "./pages/Usuarios";
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
        <Route path="/usuarios" element={<Usuarios />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/expedientes" element={<Expedientes />} />
        <Route path="/audiencias" element={<Audiencias />} />
        <Route path="/clientes" element={<Clientes />} />
        <Route path="/facturacion" element={<Facturacion />} />
        <Route path="/reportes" element={<Reportes />} />
        <Route path="/configuracion" element={<Configuracion />} />
      </Routes>
    </BrowserRouter>
  );
}