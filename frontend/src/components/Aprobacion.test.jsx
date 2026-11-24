import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

vi.mock("../api", () => ({ default: { post: vi.fn() } }));

import { AccionesAprobacion } from "./Aprobacion";

const item = (aprobacion) => ({ id: 1, aprobacion });
const montar = (aprobacion, permiso) =>
  render(<AccionesAprobacion item={item(aprobacion)} recurso="demandas" permiso={permiso} onCambio={() => {}} />);

describe("AccionesAprobacion", () => {
  it("el escribiente puede enviar un borrador pero no aprobar", () => {
    montar("borrador", { editar: true, aprobar: false });
    expect(screen.getByText("Enviar a aprobación")).toBeTruthy();
    expect(screen.queryByText("Aprobar")).toBeNull();
  });

  it("el abogado aprueba o devuelve lo pendiente", () => {
    montar("pendiente", { editar: true, aprobar: true });
    expect(screen.getByText("Aprobar")).toBeTruthy();
    expect(screen.getByText("Devolver")).toBeTruthy();
    expect(screen.queryByText("Enviar a aprobación")).toBeNull();
  });

  it("no ofrece nada sobre un escrito ya aprobado", () => {
    montar("aprobado", { editar: true, aprobar: true });
    expect(screen.queryByText("Aprobar")).toBeNull();
    expect(screen.queryByText("Enviar a aprobación")).toBeNull();
  });
});
