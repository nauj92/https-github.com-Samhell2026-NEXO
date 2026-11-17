import { describe, expect, it } from "vitest";
import { moduloDeRuta, puede, puedeVerRuta, rutaInicial } from "./permisos";

const perfil = (rol, permisos) => ({ rol, permisos });
const admin = perfil("administrador", { usuarios: "VCEX", reportes: "V", expedientes: "VCEX", clientes: "VCEX", agenda: "VCEX" });
const escribiente = perfil("escribiente", { expedientes: "V", clientes: "V", documentos: "VCE", agenda: "V" });
const dependiente = perfil("dependiente", { documentos: "C", agenda: "V" });

describe("permisos por rol", () => {
  it("lee las letras del perfil", () => {
    expect(puede(admin, "usuarios", "C")).toBe(true);
    expect(puede(escribiente, "clientes", "E")).toBe(false);
    expect(puede(null, "clientes", "V")).toBe(false);
  });

  it("asocia pantallas a módulos", () => {
    expect(moduloDeRuta("/liquidacion/laboral")).toBe("liquidaciones");
    expect(moduloDeRuta("/notificaciones")).toBe(null);
  });

  it("oculta pantallas sin permiso de ver", () => {
    expect(puedeVerRuta(escribiente, "/abogados")).toBe(false);
    expect(puedeVerRuta(escribiente, "/notificaciones")).toBe(true);
    expect(puedeVerRuta(admin, "/abogados")).toBe(true);
  });

  it("elige la pantalla inicial", () => {
    expect(rutaInicial(admin)).toBe("/dashboard");
    expect(rutaInicial(escribiente)).toBe("/expedientes");
    expect(rutaInicial(dependiente)).toBe("/audiencias");
    expect(rutaInicial(perfil("cliente", {}))).toBe("/configuracion");
  });
});
