import { describe, expect, it } from "vitest";
import { CLASES_PROCESO, DEPARTAMENTOS, ENTIDADES, ESPECIALIDADES, gruposDeClases, todasLasClases } from "./catalogos";

describe("catálogos de la Rama Judicial", () => {
  it("tienen las listas completas del portal", () => {
    expect(DEPARTAMENTOS).toHaveLength(33);
    expect(ENTIDADES).toHaveLength(17);
    expect(ESPECIALIDADES).toHaveLength(45);
  });
  it("incluyen Bogotá y la especialidad Familia", () => {
    expect(DEPARTAMENTOS).toContain("BOGOTÁ");
    expect(ESPECIALIDADES).toContain("FAMILIA");
  });
  it("no repiten elementos", () => {
    expect(new Set(DEPARTAMENTOS).size).toBe(DEPARTAMENTOS.length);
    expect(new Set(ESPECIALIDADES).size).toBe(ESPECIALIDADES.length);
  });
});

describe("gruposDeClases", () => {
  it("sin especialidad devuelve todos los grupos", () => {
    expect(gruposDeClases("")).toEqual(Object.keys(CLASES_PROCESO));
  });
  it("mezcla los grupos de las especialidades combinadas", () => {
    expect(gruposDeClases("CIVIL - FAMILIA")).toEqual(["CIVIL", "FAMILIA"]);
    expect(gruposDeClases("CIVIL - FAMILIA - LABORAL")).toEqual(["CIVIL", "FAMILIA", "LABORAL"]);
    expect(gruposDeClases("PROMISCUO / COMPETENCIA MÚLTIPLE")).toEqual(["CIVIL", "FAMILIA", "LABORAL"]);
  });
  it("relaciona especialidades con su grupo", () => {
    expect(gruposDeClases("FAMILIA ORALIDAD")).toEqual(["FAMILIA"]);
    expect(gruposDeClases("CIVIL ORALIDAD")).toEqual(["CIVIL"]);
    expect(gruposDeClases("SECCIÓN TERCERA")).toEqual(["ADMINISTRATIVA"]);
    expect(gruposDeClases("PENAL ESPECIALIZADO")).toEqual(["PENAL"]);
  });
  it("una especialidad sin demanda no tiene clases", () => {
    expect(gruposDeClases("OFICINA JUDICIAL")).toEqual([]);
  });
  it("cada grupo devuelto existe en las clases de proceso", () => {
    for (const e of ESPECIALIDADES) {
      for (const g of gruposDeClases(e)) expect(CLASES_PROCESO).toHaveProperty([g]);
    }
  });
});

describe("todasLasClases", () => {
  it("lista cada clase con su grupo", () => {
    const todas = todasLasClases();
    const total = Object.values(CLASES_PROCESO).reduce((n, l) => n + l.length, 0);
    expect(todas).toHaveLength(total);
    expect(todas.find((c) => c.value === "Divorcio").grupo).toBe("FAMILIA");
  });
});
