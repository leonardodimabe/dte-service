import { describe, expect, it } from "vitest";
import { canWrite, isAdmin } from "./auth";

describe("roles", () => {
  it("isAdmin incluye roles internos y no a client", () => {
    expect(isAdmin("superadmin")).toBe(true);
    expect(isAdmin("operator")).toBe(true);
    expect(isAdmin("auditor")).toBe(true);
    expect(isAdmin("client")).toBe(false);
    expect(isAdmin(undefined)).toBe(false);
  });

  it("canWrite solo superadmin/operator", () => {
    expect(canWrite("superadmin")).toBe(true);
    expect(canWrite("operator")).toBe(true);
    expect(canWrite("auditor")).toBe(false);
    expect(canWrite("client")).toBe(false);
  });
});
