import { describe, expect, it } from "vitest";
import { esDepartamentoBogota, esMunicipioBogota, municipioAutomatico, municipiosDe } from "./despachos";

const juzgados = [
  { departamento: "BOGOTÁ", municipio: "BOGOTÁ" },
  { departamento: "BOGOTÁ", municipio: "BOGOTÁ ANTES J 11 PENAL MUNICIPAL" },
  { departamento: "BOGOTÁ", municipio: "EJECUCIÓN DE SENTENCIAS BOGOTÁ" },
  { departamento: "BOGOTÁ", municipio: "ESTADO" },
  { departamento: "ANTIOQUIA", municipio: "MEDELLÍN" },
  { departamento: "ANTIOQUIA", municipio: "ENVIGADO" },
];

describe("filtros de despacho", () => {
  it("reconoce Bogotá con o sin tilde y con D.C.", () => {
    expect(esDepartamentoBogota("BOGOTÁ")).toBe(true);
    expect(esDepartamentoBogota("Bogota D.C.")).toBe(true);
    expect(esDepartamentoBogota("ANTIOQUIA")).toBe(false);
    expect(esMunicipioBogota("BOGOTÁ")).toBe(true);
    expect(esMunicipioBogota("BOGOTÁ D.C.")).toBe(true);
    expect(esMunicipioBogota("BOGOTÁ ANTES J 11 PENAL MUNICIPAL")).toBe(false);
    expect(esMunicipioBogota("EJECUCIÓN DE SENTENCIAS BOGOTÁ")).toBe(false);
  });

  it("con departamento Bogotá solo ofrece el municipio Bogotá", () => {
    expect(municipiosDe(juzgados, "BOGOTÁ")).toEqual(["BOGOTÁ"]);
  });

  it("conserva el municipio ya guardado al editar", () => {
    expect(municipiosDe(juzgados, "BOGOTÁ", "ESTADO")).toEqual(["BOGOTÁ", "ESTADO"]);
  });

  it("en otros departamentos ofrece todos sus municipios, ordenados", () => {
    expect(municipiosDe(juzgados, "ANTIOQUIA")).toEqual(["ENVIGADO", "MEDELLÍN"]);
    expect(municipiosDe(juzgados, "")).toHaveLength(6);
  });

  it("elige Bogotá automáticamente solo para el departamento Bogotá", () => {
    expect(municipioAutomatico(juzgados, "BOGOTÁ")).toBe("BOGOTÁ");
    expect(municipioAutomatico(juzgados, "ANTIOQUIA")).toBe("");
  });
});
