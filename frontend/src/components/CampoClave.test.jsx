import { describe, expect, it } from "vitest";
import { useState } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import CampoClave from "./CampoClave";

function Prueba() {
  const [v, setV] = useState("");
  return <CampoClave aria-label="clave" value={v} onChange={(e) => setV(e.target.value)} />;
}

describe("CampoClave", () => {
  it("oculta la contraseña por defecto y el ojo la muestra y la vuelve a ocultar", async () => {
    const user = userEvent.setup();
    render(<Prueba />);
    const campo = screen.getByLabelText("clave");
    await user.type(campo, "Secreta-123");
    expect(campo.type).toBe("password");
    await user.click(screen.getByRole("button", { name: "Mostrar contraseña" }));
    expect(campo.type).toBe("text");
    expect(campo.value).toBe("Secreta-123");
    await user.click(screen.getByRole("button", { name: "Ocultar contraseña" }));
    expect(campo.type).toBe("password");
  });
});
