/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // El SPA llama al API bajo /api; aquí se reescribe a la raíz del backend.
    // Mismo esquema que nginx en prod → dev y prod consistentes, sin colisión
    // entre las rutas de navegación (/users, /audit) y los endpoints del API.
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ""),
      },
    },
  },
  test: {
    environment: "jsdom",
    globals: false,
    setupFiles: "./src/test/setup.ts",
    css: false,
  },
});
