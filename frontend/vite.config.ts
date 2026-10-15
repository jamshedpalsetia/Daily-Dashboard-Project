import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In Compose the API is reachable as http://api:8000; on the host it is published on 8080.
const apiTarget = process.env.VITE_API_PROXY ?? "http://localhost:8080";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    watch: { usePolling: true },
    proxy: {
      "/api": { target: apiTarget, changeOrigin: true },
    },
  },
});
