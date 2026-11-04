import { beforeEach, describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import BotonTema from "./BotonTema";

describe("BotonTema", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.setAttribute("data-tema", "claro");
  });

  it("alterna entre modo nocturno y diurno", async () => {
    const user = userEvent.setup();
    render(<BotonTema etiqueta />);
    await user.click(screen.getByRole("button", { name: "Modo nocturno" }));
    expect(document.documentElement.getAttribute("data-tema")).toBe("oscuro");
    expect(localStorage.getItem("tema")).toBe("oscuro");
    await user.click(screen.getByRole("button", { name: "Modo diurno" }));
    expect(document.documentElement.getAttribute("data-tema")).toBe("claro");
  });

  it("arranca en modo nocturno si ya estaba activo", () => {
    document.documentElement.setAttribute("data-tema", "oscuro");
    render(<BotonTema />);
    expect(screen.getByRole("button", { name: "Modo diurno" })).toBeTruthy();
  });
});
