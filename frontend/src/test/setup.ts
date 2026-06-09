import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Con globals:false, RTL no registra el cleanup automático: lo hacemos aquí.
afterEach(() => cleanup());
