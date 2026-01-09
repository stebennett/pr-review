import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: "0.0.0.0",
    hmr: {
      // Explicit WebSocket configuration for Docker
      host: "localhost",
      clientPort: 3000,
      protocol: "ws",
    },
    watch: {
      // Use polling for Docker volume mounts
      usePolling: true,
      interval: 1000,
    },
  },
});
