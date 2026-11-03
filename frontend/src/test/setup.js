import { afterEach, expect } from "vitest";
import { cleanup } from "@testing-library/react";
import * as matchers from "@testing-library/jest-dom/matchers";

// Registra las comprobaciones de pantalla (toBeInTheDocument, toBeDisabled...) de forma explícita
expect.extend(matchers);

// Desmonta lo renderizado y limpia el almacenamiento entre pruebas
afterEach(() => {
  cleanup();
  localStorage.clear();
});
