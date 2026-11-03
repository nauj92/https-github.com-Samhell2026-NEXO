import { useState } from "react";
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import SelectorBuscable from "./SelectorBuscable";

const opciones = [
  { value: "1", label: "Juzgado 1 Civil del Circuito de Bogotá" },
  { value: "2", label: "Juzgado 2 de Familia de Medellín" },
  { value: "3", label: "Juzgado 3 Laboral de Cali" },
];

function Envoltorio({ alCambiar }) {
  const [valor, setValor] = useState("");
  return (
    <SelectorBuscable
      opciones={opciones}
      value={valor}
      onChange={(v) => {
        setValor(v);
        alCambiar?.(v);
      }}
      vacio="Sin asignar"
    />
  );
}

describe("SelectorBuscable", () => {
  it("muestra el texto vacío y abre la lista al hacer clic", async () => {
    const user = userEvent.setup();
    render(<Envoltorio />);
    expect(screen.getByRole("button", { name: /Sin asignar/ })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Sin asignar/ }));
    expect(screen.getByText("Juzgado 2 de Familia de Medellín")).toBeInTheDocument();
  });

  it("filtra al escribir, sin importar mayúsculas ni tildes", async () => {
    const user = userEvent.setup();
    render(<Envoltorio />);
    await user.click(screen.getByRole("button", { name: /Sin asignar/ }));
    await user.type(screen.getByPlaceholderText("Buscar…"), "BOGOTA");
    expect(screen.getByText("Juzgado 1 Civil del Circuito de Bogotá")).toBeInTheDocument();
    expect(screen.queryByText("Juzgado 3 Laboral de Cali")).not.toBeInTheDocument();
  });

  it("al elegir una opción avisa el valor y muestra su nombre", async () => {
    const user = userEvent.setup();
    const alCambiar = vi.fn();
    render(<Envoltorio alCambiar={alCambiar} />);
    await user.click(screen.getByRole("button", { name: /Sin asignar/ }));
    await user.click(screen.getByText("Juzgado 3 Laboral de Cali"));
    expect(alCambiar).toHaveBeenCalledWith("3");
    expect(screen.getByRole("button", { name: /Juzgado 3 Laboral de Cali/ })).toBeInTheDocument();
  });

  it("indica cuando la búsqueda no tiene resultados", async () => {
    const user = userEvent.setup();
    render(<Envoltorio />);
    await user.click(screen.getByRole("button", { name: /Sin asignar/ }));
    await user.type(screen.getByPlaceholderText("Buscar…"), "zzzz");
    expect(screen.getByText("Sin resultados")).toBeInTheDocument();
  });
});
