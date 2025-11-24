import i18n from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";
import baseEn from "./locales/base/en.json";
import baseRu from "./locales/base/ru.json";
import baseEs from "./locales/base/es.json";
import baseIt from "./locales/base/it.json";
import basePt from "./locales/base/pt.json";
import baseAr from "./locales/base/ar.json";
import medgEn from "./locales/medg/en.json";
import medgRu from "./locales/medg/ru.json";
import medgEs from "./locales/medg/es.json";
import medgIt from "./locales/medg/it.json";
import medgPt from "./locales/medg/pt.json";
import medgAr from "./locales/medg/ar.json";

const BRAND = import.meta.env.VITE_BRAND as "dents" | "medg" | undefined;
const isMedg = BRAND === "medg";

function deepMerge<T extends object, U extends object>(
  base: T,
  override?: U,
): T & U {
  if (!override) return base as T & U;
  const result: any = Array.isArray(base) ? [...(base as any)] : { ...base };

  for (const key of Object.keys(override)) {
    const baseVal = (base as any)[key];
    const overVal = (override as any)[key];

    if (
      baseVal &&
      typeof baseVal === "object" &&
      !Array.isArray(baseVal) &&
      overVal &&
      typeof overVal === "object" &&
      !Array.isArray(overVal)
    ) {
      result[key] = deepMerge(baseVal, overVal);
    } else {
      result[key] = overVal;
    }
  }

  return result;
}

const resources = {
  EN: {
    translation: isMedg ? deepMerge(baseEn, medgEn) : (baseEn as typeof baseEn),
  },
  RU: {
    translation: isMedg ? deepMerge(baseRu, medgRu) : (baseRu as typeof baseRu),
  },
  ES: {
    translation: isMedg ? deepMerge(baseEs, medgEs) : (baseEs as typeof baseEs),
  },
  IT: {
    translation: isMedg ? deepMerge(baseIt, medgIt) : (baseIt as typeof baseIt),
  },
  PT: {
    translation: isMedg ? deepMerge(basePt, medgPt) : (basePt as typeof basePt),
  },
  AR: {
    translation: isMedg ? deepMerge(baseAr, medgAr) : (baseAr as typeof baseAr),
  },
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    debug: false,
    fallbackLng: "EN",
    lng: "EN",
    resources,
    interpolation: {
      escapeValue: false,
      format: (value, format, lng) => {
        if (format === "localizedNumber" && typeof value === "number") {
          const locale = lng?.toLowerCase?.() || "en";
          if (locale === "ar") {
            return new Intl.NumberFormat("ar", {
              numberingSystem: "arab",
            }).format(value);
          }

          return new Intl.NumberFormat(locale).format(value);
        }
        return value;
      },
    },
  });

export default i18n;
