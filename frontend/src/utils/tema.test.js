import { beforeEach, describe, expect, it } from "vitest";
import { aplicarTema, temaGuardado } from "./tema";

describe("tema", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute("data-tema");
  });

  it("por defecto es diurno", () => {
    expect(temaGuardado()).toBe("claro");
  });

  it("aplica y recuerda el modo nocturno", () => {
    expect(aplicarTema("oscuro")).toBe("oscuro");
    expect(document.documentElement.getAttribute("data-tema")).toBe("oscuro");
    expect(temaGuardado()).toBe("oscuro");
  });

  it("vuelve al modo diurno", () => {
    aplicarTema("oscuro");
    expect(aplicarTema("claro")).toBe("claro");
    expect(document.documentElement.getAttribute("data-tema")).toBe("claro");
    expect(temaGuardado()).toBe("claro");
  });

  it("ignora valores desconocidos", () => {
    expect(aplicarTema("otro")).toBe("claro");
  });
});
