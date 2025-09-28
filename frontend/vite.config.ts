import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";
import svgr from "vite-plugin-svgr";

export default defineConfig({
  plugins: [react(), svgr()],
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
