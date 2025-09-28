import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react-swc"; // ← было @vitejs/plugin-react
import path from "node:path";
import svgr from "vite-plugin-svgr"; // оставляем как есть

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
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
          additionalData: `@use "${env.VITE_GLOBAL_STYLE}" as *;`,
        },
      },
    },
    resolve: {
      alias: {
        "@": path.resolve("src"),
        "@locales": path.resolve(
          __dirname,
          `src/i18n/locales/${env.VITE_BRAND}`,
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
