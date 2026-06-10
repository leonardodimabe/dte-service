import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import Audit from "./Audit";

vi.mock("../api", () => ({
  api: {
    auditRequests: vi.fn().mockResolvedValue([]),
    auditChanges: vi.fn().mockResolvedValue([]),
    downloadAuditCsv: vi.fn(),
  },
}));
vi.mock("../auth", async (orig) => {
  const actual = await orig<typeof import("../auth")>();
  return {
    ...actual,
    useAuth: () => ({
      user: { id: 9, email: "c@x.cl", role: "client", customer_id: 3 },
      loading: false,
      login: vi.fn(),
      logout: vi.fn(),
    }),
  };
});

describe("Audit", () => {
  it("el rol client no ve la pestaña de Cambios", async () => {
    render(<Audit />);
    expect(await screen.findByRole("button", { name: "Peticiones" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Cambios" })).toBeNull();
  });
});
