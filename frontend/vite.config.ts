import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// El target del proxy se resuelve por variable de entorno (VITE_PROXY_TARGET).
// Si no está definida, se usa localhost:8000 — útil para desarrollo local.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const proxyTarget = env.VITE_PROXY_TARGET || "http://localhost:8000";

  return {
    plugins: [react()],
    server: {
      port: 5173,
      host: "0.0.0.0",
      proxy: {
        "/api": { target: proxyTarget, changeOrigin: true },
      },
    },
  };
});
