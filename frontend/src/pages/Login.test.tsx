import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import Login from "./Login";

const { login, navigate } = vi.hoisted(() => ({ login: vi.fn(), navigate: vi.fn() }));
vi.mock("../auth", () => ({ useAuth: () => ({ login }) }));
vi.mock("react-router-dom", () => ({ useNavigate: () => navigate }));

describe("Login", () => {
  it("envía las credenciales escritas", async () => {
    login.mockResolvedValueOnce(undefined);
    const { container } = render(<Login />);
    await userEvent.type(screen.getByRole("textbox"), "a@b.cl");
    await userEvent.type(container.querySelector('input[type="password"]') as HTMLElement, "pw");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));
    expect(login).toHaveBeenCalledWith("a@b.cl", "pw");
  });

  it("muestra el error si el login falla", async () => {
    login.mockRejectedValueOnce(new Error("credenciales inválidas"));
    const { container } = render(<Login />);
    await userEvent.type(screen.getByRole("textbox"), "a@b.cl");
    await userEvent.type(container.querySelector('input[type="password"]') as HTMLElement, "x");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));
    expect(await screen.findByText("credenciales inválidas")).toBeInTheDocument();
  });
});
