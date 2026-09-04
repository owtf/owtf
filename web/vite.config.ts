import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  server: { proxy: { "/api": process.env.OWTF_DEV_API || "http://127.0.0.1:8009" } },
  build: {
    outDir: "../internal/api/ui",
    emptyOutDir: true,
    assetsDir: "assets",
  },
});
