// Permisos por rol (espejo de la matriz del backend: core/permisos.py).
// El backend es quien manda; esto solo decide qué se muestra. El perfil trae `permisos`: {modulo: "VCE"}.
import { useEffect, useState } from "react";
import api from "../api";

export const ROLES = [
  ["administrador", "Administrador"],
  ["abogado", "Abogado"],
  ["secretario_juridico", "Secretaria"],
  ["escribiente", "Escribiente"],
  ["dependiente", "Dependiente"],
  ["cliente", "Cliente"],
];

export const nombreRol = (rol) => (ROLES.find((r) => r[0] === rol) || [])[1] || rol || "";

export const puede = (perfil, modulo, letra) => !!perfil?.permisos?.[modulo]?.includes(letra);

// Módulo de la matriz al que pertenece cada pantalla
const MODULO_POR_RUTA = [
  ["/dashboard", "reportes"],
  ["/liquidacion", "liquidaciones"],
  ["/vigilancia", "vigilancia"],
  ["/demandas", "documentos"],
  ["/contestaciones", "documentos"],
  ["/citaciones", "documentos"],
  ["/clientes", "clientes"],
  ["/abogados", "usuarios"],
  ["/audiencias", "agenda"],
  ["/acuerdos", "finanzas"],
  ["/expedientes", "expedientes"],
];

export const moduloDeRuta = (ruta) => (MODULO_POR_RUTA.find(([p]) => ruta.startsWith(p)) || [])[1] || null;

// ¿Puede el usuario abrir esta pantalla? Las rutas fuera de la matriz (perfil, notificaciones) son libres.
export const puedeVerRuta = (perfil, ruta) => {
  const modulo = moduloDeRuta(ruta);
  return modulo === null || puede(perfil, modulo, "V");
};

// Primera pantalla a la que puede entrar el usuario al iniciar sesión
export const rutaInicial = (perfil) => {
  if (!perfil) return "/dashboard";
  if (perfil.rol === "cliente") return "/configuracion";
  const orden = ["/dashboard", "/expedientes", "/audiencias", "/demandas", "/clientes", "/acuerdos", "/liquidacion/laboral"];
  return orden.find((r) => puedeVerRuta(perfil, r)) || "/notificaciones";
};

// Hook: permisos del usuario en un módulo -> { ver, crear, editar, eliminar, aprobar, perfil }
// El perfil se guarda por sesión (clave = token), así otro usuario en el mismo navegador no hereda permisos.
let cache = { token: null, perfil: null };
const tokenActual = () => {
  try {
    return localStorage.getItem("access_token");
  } catch {
    return null;
  }
};
const perfilVigente = () => (cache.token === tokenActual() ? cache.perfil : null);

export function usePermisos(modulo) {
  const [perfil, setPerfil] = useState(perfilVigente);
  useEffect(() => {
    if (perfilVigente()) return;
    api
      .get("/perfil/")
      .then((r) => { cache = { token: tokenActual(), perfil: r.data }; setPerfil(r.data); })
      .catch(() => {});
  }, []);
  return {
    perfil,
    ver: puede(perfil, modulo, "V"),
    crear: puede(perfil, modulo, "C"),
    editar: puede(perfil, modulo, "E"),
    eliminar: puede(perfil, modulo, "X"),
    aprobar: puede(perfil, modulo, "A"),
  };
}
