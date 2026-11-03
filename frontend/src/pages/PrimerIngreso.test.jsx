import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";

vi.mock("../api", () => ({ default: { get: vi.fn(), post: vi.fn() } }));
import api from "../api";
import PrimerIngreso from "./PrimerIngreso";

const perfil = (extra = {}) => ({
  data: { first_name: "Ana", username: "ana", rol: "abogado", debe_cambiar_password: true, autorizacion_datos_pendiente: true, ...extra },
});

const dibujar = () =>
  render(
    <MemoryRouter>
      <PrimerIngreso />
    </MemoryRouter>
  );

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.setItem("access_token", "token-de-prueba");
});

describe("Primer ingreso", () => {
  it("empieza por el cambio de contraseña", async () => {
    api.get.mockResolvedValue(perfil());
    dibujar();
    expect(await screen.findByText(/Paso 1 de 2/)).toBeInTheDocument();
  });

  it("no envía nada si las contraseñas nuevas no coinciden", async () => {
    api.get.mockResolvedValue(perfil());
    const user = userEvent.setup();
    const { container } = dibujar();
    await screen.findByText(/Paso 1 de 2/);
    const [actual, nueva, repetir] = container.querySelectorAll('input[type="password"]');
    await user.type(actual, "Temporal-123");
    await user.type(nueva, "Mi-Clave-Nueva-55");
    await user.type(repetir, "Otra-Clave-Distinta");
    await user.click(screen.getByRole("button", { name: /Guardar y continuar/ }));
    expect(screen.getByText(/no coinciden/)).toBeInTheDocument();
    expect(api.post).not.toHaveBeenCalled();
  });

  it("rechaza una contraseña nueva igual a la temporal", async () => {
    api.get.mockResolvedValue(perfil());
    const user = userEvent.setup();
    const { container } = dibujar();
    await screen.findByText(/Paso 1 de 2/);
    const [actual, nueva, repetir] = container.querySelectorAll('input[type="password"]');
    await user.type(actual, "Temporal-123");
    await user.type(nueva, "Temporal-123");
    await user.type(repetir, "Temporal-123");
    await user.click(screen.getByRole("button", { name: /Guardar y continuar/ }));
    expect(screen.getByText(/distinta de la temporal/)).toBeInTheDocument();
    expect(api.post).not.toHaveBeenCalled();
  });

  it("cambia la contraseña y pasa a la autorización de datos", async () => {
    api.get.mockResolvedValueOnce(perfil()).mockResolvedValueOnce(perfil({ debe_cambiar_password: false }));
    api.post.mockResolvedValue({ data: {} });
    const user = userEvent.setup();
    const { container } = dibujar();
    await screen.findByText(/Paso 1 de 2/);
    const [actual, nueva, repetir] = container.querySelectorAll('input[type="password"]');
    await user.type(actual, "Temporal-123");
    await user.type(nueva, "Mi-Clave-Nueva-55");
    await user.type(repetir, "Mi-Clave-Nueva-55");
    await user.click(screen.getByRole("button", { name: /Guardar y continuar/ }));
    expect(api.post).toHaveBeenCalledWith("/perfil/cambiar-password/", { password_actual: "Temporal-123", password_nueva: "Mi-Clave-Nueva-55" });
    expect(await screen.findByText(/Paso 2 de 2/)).toBeInTheDocument();
  });

  it("la autorización exige marcar la casilla antes de continuar", async () => {
    api.get.mockResolvedValue(perfil({ debe_cambiar_password: false }));
    const user = userEvent.setup();
    dibujar();
    await screen.findByText(/Paso 2 de 2/);
    const boton = screen.getByRole("button", { name: /Autorizo y entrar/ });
    expect(boton).toBeDisabled();
    await user.click(screen.getByRole("checkbox"));
    expect(boton).toBeEnabled();
    api.post.mockResolvedValue({ data: {} });
    await user.click(boton);
    await waitFor(() => expect(api.post).toHaveBeenCalledWith("/perfil/autorizar-datos/", { acepto: true }));
  });
});
