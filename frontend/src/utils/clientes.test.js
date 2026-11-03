import { describe, expect, it } from "vitest";
import { aplicarClienteAParte, clienteComoParte, completarVacios, ordenarPorNombre } from "./clientes";

const persona = { id: 7, nombre: "María Pérez", tipo_documento: "CC", numero_documento: "123456789", email: "maria@correo.com", direccion: "Calle 1 # 2-3" };
const empresa = { id: 8, nombre: "Constructora Horizonte S.A.S.", tipo_documento: "NIT", numero_documento: "900123456", email: "", direccion: "" };

describe("clienteComoParte", () => {
  it("una persona natural con cédula", () => {
    expect(clienteComoParte(persona, "demandante")).toEqual({
      demandante: "María Pérez",
      demandante_tipo_persona: "natural",
      demandante_tipo_documento: "CC",
      demandante_documento: "123456789",
      notif_demandante_email: "maria@correo.com",
      notif_demandante_direccion: "Calle 1 # 2-3",
    });
  });
  it("un NIT es persona jurídica", () => {
    expect(clienteComoParte(empresa, "demandado").demandado_tipo_persona).toBe("juridica");
  });
  it("el pasaporte del cliente (PA) se traduce a PAS del formulario", () => {
    expect(clienteComoParte({ ...persona, tipo_documento: "PA" }, "demandado").demandado_tipo_documento).toBe("PAS");
  });
});

describe("completarVacios", () => {
  it("no pisa lo que el usuario ya escribió", () => {
    expect(completarVacios({ a: "escrito", b: "" }, { a: "nuevo", b: "nuevo", c: "nuevo" })).toEqual({ a: "escrito", b: "nuevo", c: "nuevo" });
  });
  it("no copia valores vacíos", () => {
    expect(completarVacios({ a: "" }, { a: "" })).toEqual({ a: "" });
  });
});

describe("aplicarClienteAParte", () => {
  it("con la parte vacía la completa con los datos del cliente", () => {
    const r = aplicarClienteAParte({ demandante: "", demandante_documento: "" }, persona, "demandante");
    expect(r.cliente).toBe(7);
    expect(r.demandante).toBe("María Pérez");
    expect(r.demandante_documento).toBe("123456789");
    expect(r.notif_demandante_email).toBe("maria@correo.com");
  });
  it("si la parte ya tiene datos, solo selecciona al cliente", () => {
    const r = aplicarClienteAParte({ demandante: "Otro nombre", demandante_documento: "" }, persona, "demandante");
    expect(r.cliente).toBe(7);
    expect(r.demandante).toBe("Otro nombre");
  });
});

describe("ordenarPorNombre", () => {
  it("ordena alfabéticamente en español sin modificar la lista original", () => {
    const lista = [{ nombre: "Óscar" }, { nombre: "Ana" }, { nombre: "Zoila" }];
    expect(ordenarPorNombre(lista).map((c) => c.nombre)).toEqual(["Ana", "Óscar", "Zoila"]);
    expect(lista[0].nombre).toBe("Óscar");
  });
});
