import { describe, expect, it } from "vitest";
import { useState } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import CampoFechaHora, { partirFechaHora, unirFechaHora } from "./CampoFechaHora";

function Prueba({ inicial = "" }) {
  const [v, setV] = useState(inicial);
  return (
    <>
      <CampoFechaHora value={v} onChange={setV} />
      <output data-testid="valor">{v}</output>
    </>
  );
}

describe("CampoFechaHora", () => {
  it("convierte entre el formato del servidor y las partes (12 h)", () => {
    expect(partirFechaHora("2026-09-14T19:35")).toEqual({ fecha: "2026-09-14", hora: "7", minuto: "35", jornada: "p" });
    expect(partirFechaHora("2026-01-01T00:05")).toEqual({ fecha: "2026-01-01", hora: "12", minuto: "05", jornada: "a" });
    expect(partirFechaHora("2026-01-01T12:00")).toEqual({ fecha: "2026-01-01", hora: "12", minuto: "00", jornada: "p" });
    expect(unirFechaHora({ fecha: "2026-11-09", hora: "12", minuto: "30", jornada: "a" })).toBe("2026-11-09T00:30");
    expect(unirFechaHora({ fecha: "2026-11-09", hora: "7", minuto: "35", jornada: "" })).toBe("");
  });

  it("solo da un valor cuando están fecha, hora, minuto y jornada", async () => {
    const user = userEvent.setup();
    render(<Prueba />);
    fireEvent.change(screen.getByLabelText("Fecha"), { target: { value: "2026-11-09" } });
    await user.selectOptions(screen.getByLabelText("Hora"), "7");
    await user.selectOptions(screen.getByLabelText("Minuto"), "35");
    expect(screen.getByTestId("valor").textContent).toBe("");
    await user.selectOptions(screen.getByLabelText("Jornada"), "p");
    expect(screen.getByTestId("valor").textContent).toBe("2026-11-09T19:35");
  });

  it("muestra el valor recibido al editar", () => {
    render(<Prueba inicial="2026-09-14T09:15" />);
    expect(screen.getByLabelText("Fecha").value).toBe("2026-09-14");
    expect(screen.getByLabelText("Hora").value).toBe("9");
    expect(screen.getByLabelText("Minuto").value).toBe("15");
    expect(screen.getByLabelText("Jornada").value).toBe("a");
  });
});
