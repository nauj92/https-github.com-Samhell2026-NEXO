import { describe, expect, it } from "vitest";
import { fecha, limpiar, pesos } from "./formato";

describe("fecha", () => {
  it("convierte AAAA-MM-DD en DD/MM/AAAA sin corrimiento de zona horaria", () => {
    expect(fecha("2026-10-15")).toBe("15/10/2026");
    expect(fecha("2027-01-01T00:00:00Z")).toBe("01/01/2027");
  });
  it("muestra una raya si no hay fecha", () => {
    expect(fecha("")).toBe("—");
    expect(fecha(null)).toBe("—");
  });
});

describe("pesos", () => {
  it("formatea en pesos colombianos sin decimales", () => {
    const texto = pesos(1500000);
    expect(texto).toMatch(/1\.500\.000/);
    expect(texto).not.toMatch(/,00/);
  });
  it("acepta texto numérico y vacíos", () => {
    expect(pesos("25000")).toMatch(/25\.000/);
    expect(pesos(null)).toBe("—");
    expect(pesos("")).toBe("—");
  });
});

describe("limpiar", () => {
  it("quita los campos vacíos pero conserva el cero y el falso", () => {
    expect(limpiar({ a: "", b: null, c: undefined, d: 0, e: false, f: "x" })).toEqual({ d: 0, e: false, f: "x" });
  });
});
