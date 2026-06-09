import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi, type Mock } from "vitest";
import { api } from "../api";
import Customers from "./Customers";

vi.mock("../api", () => ({
  api: { customers: vi.fn() },
  getToken: vi.fn(),
  setToken: vi.fn(),
}));
vi.mock("../auth", async (orig) => {
  const actual = await orig<typeof import("../auth")>();
  return {
    ...actual,
    useAuth: () => ({
      user: { id: 1, email: "op@x.cl", role: "operator", customer_id: null },
      loading: false,
      login: vi.fn(),
      logout: vi.fn(),
    }),
  };
});

describe("Customers", () => {
  it("lista clientes y muestra el alta para operador", async () => {
    (api.customers as Mock).mockResolvedValue([
      { id: 1, name: "ACME", key: "acme", rut: "76158145-7", environment: "CERTIFICATION" },
    ]);
    render(
      <MemoryRouter>
        <Customers />
      </MemoryRouter>,
    );
    expect(await screen.findByText("ACME")).toBeInTheDocument();
    expect(screen.getByText("Nuevo cliente")).toBeInTheDocument();
  });
});
