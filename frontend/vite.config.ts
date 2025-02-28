import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `@use "@/styles/_global.scss" as *;`,
      },
    },
  },
  resolve: {
    alias: {
      "@": path.resolve("src"),
    },
  },
});
