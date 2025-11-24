import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react-swc"; // ← было @vitejs/plugin-react
import path from "node:path";
import svgr from "vite-plugin-svgr"; // оставляем как есть

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const brand = env.VITE_BRAND || "dents";
  const themeFile = brand === "medg" ? "_theme-medg.scss" : "_theme-dents.scss";

  return {
    plugins: [
      react(),
      svgr(), // без изменений
    ],
    css: {
      // включаем параллелизм SCSS (в резолв-конфиге у тебя было 0 = без воркеров)
      // свойство поддерживается в Vite 5/6, если вдруг не примется — просто убери
      preprocessorMaxWorkers: -1,
      devSourcemap: false,
      preprocessorOptions: {
        scss: {
          additionalData: `@use "@/app/styles/${themeFile}" as *;`,
        },
      },
    },
    resolve: {
      alias: {
        "@": path.resolve("src"),
        "@locales": path.resolve(__dirname, `src/app/i18n/locales`),

        "@hero-bg": path.resolve(
          brand === "medg"
            ? "src/shared/assets/hero-background-medg.webp"
            : "src/shared/assets/hero-background.webp",
        ),
        "@hero-bg-mobile": path.resolve(
          brand === "medg"
            ? "src/shared/assets/hero-background-mobile-medg.webp"
            : "src/shared/assets/hero-background-mobile.webp",
        ),
        "@logo": path.resolve(
          brand === "medg"
            ? "src/shared/assets/logos/logo-medg.svg?react"
            : "src/shared/assets/logos/logo.svg?react",
        ),
      },

      dedupe: ["react", "react-dom"],
    },
    build: {
      target: ["es2022", "chrome107", "firefox102", "safari15.4"],
      minify: "esbuild",
      cssMinify: "esbuild",
      sourcemap: false,
      reportCompressedSize: false, // не считаем gzip/brotli
      // чуть разгружаем rollup фазу
      rollupOptions: {
        output: {
          manualChunks: {
            react: ["react", "react-dom"],
            i18n: [
              "i18next",
              "react-i18next",
              "i18next-browser-languagedetector",
            ],
            charts: ["recharts"],
            media: ["swiper"],
            ui: [
              "axios",
              "react-select",
              "sweetalert2",
              "sweetalert2-react-content",
              "joi",
            ],
          },
        },
        // убираем лишние предупреждения от commonjs
        onwarn(w, warn) {
          if (w.code === "CIRCULAR_DEPENDENCY") return;
          warn(w);
        },
      },
      assetsInlineLimit: 0, // не инлайнить base64 (чуть быстрее)
    },
  };
});
