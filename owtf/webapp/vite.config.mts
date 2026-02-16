import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      containers: path.resolve(__dirname, "src/containers"),
      "style.scss": path.resolve(__dirname, "src/style.scss"),
    },
  },
  server: {
    host: "0.0.0.0",
    port: 3000,
    strictPort: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8009",
        changeOrigin: true,
      },
      "/debug": {
        target: "http://127.0.0.1:8009",
        changeOrigin: true,
      },
      "/logs": {
        target: "http://127.0.0.1:8009",
        changeOrigin: true,
      },
      "/output_files": {
        target: "http://127.0.0.1:8009",
        changeOrigin: true,
      },
    },
  },
  preview: {
    host: "0.0.0.0",
    port: 4173,
    strictPort: true,
  },
  build: {
    outDir: "build",
    assetsDir: "static",
    emptyOutDir: true,
    sourcemap: true,
  },
  css: {
    preprocessorOptions: {
      scss: {
        api: "modern-compiler",
      },
    },
  },
});
