import en from "./locales/en.json";
import ru from "./locales/ru.json";
import es from "./locales/es.json";

import i18n from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    debug: false,
    fallbackLng: "en",
    lng: "en",
    interpolation: {
      escapeValue: false,
    },
    resources: {
      en: { translation: en },
      ru: { translation: ru },
      es: { translation: es },
    },
  });

export default i18n;
