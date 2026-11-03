import { describe, expect, it } from "vitest";
import { mensajeError } from "./errores";

const error = (status, data) => ({ response: { status, data } });

describe("mensajeError", () => {
  it("avisa cuando no hay conexión con el servidor", () => {
    expect(mensajeError(new Error("Network Error"))).toMatch(/No hay conexión/);
  });

  it("traduce los códigos HTTP más comunes", () => {
    expect(mensajeError(error(401))).toMatch(/sesión expiró/);
    expect(mensajeError(error(404))).toMatch(/no existe/);
    expect(mensajeError(error(429))).toMatch(/Demasiados intentos/);
    expect(mensajeError(error(500))).toMatch(/Error del servidor/);
  });

  it("en 403 muestra el motivo que envía el servidor", () => {
    expect(mensajeError(error(403, { detail: "Solo el administrador puede crear o modificar usuarios." }))).toBe(
      "Solo el administrador puede crear o modificar usuarios."
    );
    expect(mensajeError(error(403, {}))).toMatch(/No tiene permiso/);
  });

  it("convierte los errores de validación en líneas con el nombre del campo", () => {
    const texto = mensajeError(error(400, { numero: ["Radicado inválido."], monto: ["Debe ser positivo."] }));
    expect(texto).toBe("Radicado: Radicado inválido.\nMonto: Debe ser positivo.");
  });

  it("no antepone etiqueta a los errores generales", () => {
    expect(mensajeError(error(400, { non_field_errors: ["Datos incompletos."] }))).toBe("Datos incompletos.");
    expect(mensajeError(error(400, { detail: "Contraseña incorrecta." }))).toBe("Contraseña incorrecta.");
  });

  it("usa el mensaje por defecto si no hay detalle", () => {
    expect(mensajeError(error(400, {}), "No se pudo guardar.")).toBe("No se pudo guardar.");
  });
});
