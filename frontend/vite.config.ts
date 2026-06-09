/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Proxy del API en dev para evitar CORS (ajusta el target si cambia).
    proxy: {
      "/auth": "http://localhost:8000",
      "/users": "http://localhost:8000",
      "/audit": "http://localhost:8000",
      "/admin": "http://localhost:8000",
    },
  },
  test: {
    environment: "jsdom",
    globals: false,
    setupFiles: "./src/test/setup.ts",
    css: false,
  },
});
