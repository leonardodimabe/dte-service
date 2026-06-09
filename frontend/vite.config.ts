import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

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
});
