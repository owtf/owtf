import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  server: {
    watch: { usePolling: true, interval: 500 },
    proxy: {
      "/api": {
        target: process.env.OWTF_DEV_API || "http://127.0.0.1:8009",
        // Preserve the browser origin for the API's same-origin command check.
        changeOrigin: false,
      },
    },
  },
  build: {
    outDir: "../internal/api/ui",
    emptyOutDir: true,
    assetsDir: "assets",
  },
});
