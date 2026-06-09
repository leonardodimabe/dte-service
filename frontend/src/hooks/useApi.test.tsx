import { renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { useApi } from "./useApi";

describe("useApi", () => {
  it("pasa de loading a data", async () => {
    const { result } = renderHook(() => useApi(() => Promise.resolve(42), []));
    expect(result.current.loading).toBe(true);
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toBe(42);
    expect(result.current.error).toBeNull();
  });

  it("captura el error del fetcher", async () => {
    const { result } = renderHook(() => useApi(() => Promise.reject(new Error("boom")), []));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBe("boom");
    expect(result.current.data).toBeNull();
  });
});
