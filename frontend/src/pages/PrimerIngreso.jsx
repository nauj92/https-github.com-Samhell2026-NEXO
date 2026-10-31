import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import { mensajeError } from "../utils/errores";
import AuthLayout, { Aviso, estiloInput, estiloBoton } from "../components/AuthLayout";

// Texto de la autorización (Ley 1581 de 2012 y Decreto 1377 de 2013, Colombia).
// El despacho debe revisarlo con su asesor jurídico y ajustarlo a su política de tratamiento de datos.
const TEXTO_AUTORIZACION = [
  ["Responsable del tratamiento", "El despacho jurídico que administra esta plataforma (Lex·ERP) es el responsable del tratamiento de los datos personales que usted registra o que se generan en el uso del sistema."],
  ["Datos que se tratan", "Nombre, documento de identidad, tarjeta profesional, correo electrónico, teléfono, rol dentro del despacho, registros de ingreso y actividad en la plataforma, y la información de los procesos, clientes y partes que usted gestione."],
  ["Finalidades", "Crear y administrar su cuenta, controlar el acceso y la seguridad, asignarle y hacer seguimiento a los procesos y términos, generar y firmar escritos judiciales, enviarle notificaciones y avisos del servicio, y cumplir obligaciones legales y contractuales."],
  ["Derechos del titular", "Usted puede conocer, actualizar, rectificar y solicitar la supresión de sus datos, pedir prueba de esta autorización, ser informado del uso que se les ha dado, revocar la autorización y presentar quejas ante la Superintendencia de Industria y Comercio."],
  ["Datos sensibles y de terceros", "Los procesos pueden contener datos sensibles o de menores de edad. Usted se compromete a tratarlos con reserva profesional, a usarlos solo para las finalidades del despacho y a no compartirlos por fuera de la plataforma."],
  ["Ejercicio de sus derechos", "Para consultas o reclamos sobre sus datos, comuníquese con el administrador del sistema. Esta autorización queda registrada con su fecha y hora de aceptación."],
];

export default function PrimerIngreso() {
  const navigate = useNavigate();
  const [perfil, setPerfil] = useState(null);
  const [msg, setMsg] = useState(null);
  const [enviando, setEnviando] = useState(false);
  const [f, setF] = useState({ actual: "", nueva: "", repetir: "" });
  const [acepto, setAcepto] = useState(false);

  const cargar = () =>
    api
      .get("/perfil/")
      .then((r) => {
        const p = r.data;
        setPerfil(p);
        if (!p.debe_cambiar_password && !p.autorizacion_datos_pendiente) navigate(p.rol === "cliente" ? "/configuracion" : "/dashboard", { replace: true });
      })
      .catch(() => navigate("/login", { replace: true }));

  useEffect(() => {
    if (!localStorage.getItem("access_token")) return navigate("/login", { replace: true });
    cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const cerrarSesion = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    navigate("/login");
  };

  const cambiarClave = async (e) => {
    e.preventDefault();
    setMsg(null);
    if (f.nueva.length < 8) return setMsg({ tipo: "error", texto: "La contraseña nueva debe tener al menos 8 caracteres." });
    if (f.nueva === f.actual) return setMsg({ tipo: "error", texto: "La contraseña nueva debe ser distinta de la temporal." });
    if (f.nueva !== f.repetir) return setMsg({ tipo: "error", texto: "Las contraseñas nuevas no coinciden." });
    setEnviando(true);
    try {
      await api.post("/perfil/cambiar-password/", { password_actual: f.actual, password_nueva: f.nueva });
      setF({ actual: "", nueva: "", repetir: "" });
      await cargar();
    } catch (err) {
      setMsg({ tipo: "error", texto: mensajeError(err) });
    } finally {
      setEnviando(false);
    }
  };

  const autorizar = async (e) => {
    e.preventDefault();
    setMsg(null);
    if (!acepto) return setMsg({ tipo: "error", texto: "Para continuar debe marcar la casilla de autorización." });
    setEnviando(true);
    try {
      await api.post("/perfil/autorizar-datos/", { acepto: true });
      await cargar();
    } catch (err) {
      setMsg({ tipo: "error", texto: mensajeError(err) });
    } finally {
      setEnviando(false);
    }
  };

  if (!perfil) return <AuthLayout titulo="Cargando…" />;

  const paso1 = perfil.debe_cambiar_password;
  const etiqueta = { fontSize: "13px", fontWeight: 600 };

  return (
    <AuthLayout titulo={paso1 ? "Paso 1 de 2 · Cambie su contraseña" : "Paso 2 de 2 · Autorización de datos personales"} ancho={paso1 ? 380 : 560}>
      {msg && <Aviso tipo={msg.tipo}>{msg.texto}</Aviso>}

      {paso1 ? (
        <form onSubmit={cambiarClave}>
          <p style={{ fontSize: "13px", color: "#4a5a70", marginTop: 0 }}>
            Hola {perfil.first_name || perfil.username}. Ingresó con una contraseña temporal; defina una propia para continuar.
          </p>
          <label style={etiqueta}>Contraseña temporal (la del correo)</label>
          <input style={{ ...estiloInput, marginTop: "6px" }} type="password" value={f.actual} onChange={(e) => setF({ ...f, actual: e.target.value })} autoComplete="current-password" />
          <label style={etiqueta}>Contraseña nueva</label>
          <input style={{ ...estiloInput, marginTop: "6px" }} type="password" value={f.nueva} onChange={(e) => setF({ ...f, nueva: e.target.value })} autoComplete="new-password" />
          <label style={etiqueta}>Repetir contraseña nueva</label>
          <input style={{ ...estiloInput, marginTop: "6px" }} type="password" value={f.repetir} onChange={(e) => setF({ ...f, repetir: e.target.value })} autoComplete="new-password" />
          <button type="submit" disabled={enviando} style={{ ...estiloBoton, opacity: enviando ? 0.7 : 1 }}>
            {enviando ? "Guardando..." : "Guardar y continuar"}
          </button>
        </form>
      ) : (
        <form onSubmit={autorizar}>
          <div style={{ maxHeight: "300px", overflowY: "auto", border: "1px solid #e5e9ef", borderRadius: "10px", padding: "12px 14px", marginBottom: "14px", background: "#f8fafc", fontSize: "13px", color: "#2b3a4d" }}>
            <p style={{ marginTop: 0 }}>
              De conformidad con la Ley 1581 de 2012 y el Decreto 1377 de 2013 (protección de datos personales), le informamos cómo se tratarán sus datos:
            </p>
            {TEXTO_AUTORIZACION.map(([t, c]) => (
              <p key={t} style={{ margin: "0 0 10px" }}>
                <strong>{t}.</strong> {c}
              </p>
            ))}
          </div>
          <label style={{ display: "flex", gap: "10px", alignItems: "flex-start", fontSize: "13px", marginBottom: "16px", cursor: "pointer" }}>
            <input type="checkbox" checked={acepto} onChange={(e) => setAcepto(e.target.checked)} style={{ marginTop: "3px" }} />
            <span>He leído la información anterior y autorizo de manera libre, previa y expresa el tratamiento de mis datos personales.</span>
          </label>
          <button type="submit" disabled={enviando || !acepto} style={{ ...estiloBoton, opacity: enviando || !acepto ? 0.6 : 1 }}>
            {enviando ? "Registrando..." : "Autorizo y entrar al sistema"}
          </button>
        </form>
      )}

      <p style={{ textAlign: "center", marginTop: "16px", fontSize: "13px" }}>
        <button type="button" onClick={cerrarSesion} style={{ background: "none", border: "none", color: "#4a5a70", textDecoration: "underline", cursor: "pointer" }}>
          Cerrar sesión
        </button>
      </p>
    </AuthLayout>
  );
}
