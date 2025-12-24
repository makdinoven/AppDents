import { t } from "i18next";
import {
  CDN_ORIGIN,
  LANGUAGES,
  LS_TOKEN_KEY,
  PAGE_SOURCES,
  PAYMENT_SOURCES,
  PAYMENT_TYPES,
} from "./commonConstants.ts";
import { ResultLandingData } from "../../store/slices/mainSlice.ts";
import { PATHS } from "../../../app/routes/routes.ts";

export const getAuthHeaders = () => {
  const accessToken = localStorage.getItem(LS_TOKEN_KEY);

  if (!accessToken) {
    throw new Error("No access token found");
  }

  return {
    Authorization: `Bearer ${accessToken}`,
  };
};

export const generateId = () => Math.floor(Math.random() * 100000);

export const formatAuthorsDesc = (authors: any, showBy: boolean = true) => {
  return authors?.length > 0
    ? `${showBy ? t("landing.by") : ""} ${
        authors
          ?.slice(0, 3)
          .map((author: any) => capitalizeText(author.name))
          .join(", ") + (authors.length > 3 ? ` ${t("etAl")}` : "")
      }`
    : null;
};

const getCookie = (name: any) => {
  const match = document.cookie.match(new RegExp(`(^| )${name}=([^;]+)`));
  return match ? match[2] : null;
};

export const getFacebookData = () => {
  const fbp = getCookie("_fbp") || "";
  const fbc = getCookie("_fbc") || "";
  return { fbp, fbc };
};

export const transformTags = (
  tags: { id: number; name: string }[],
): { id: number; name: string; value: string }[] => {
  const transformed = tags.map((tag) => ({
    ...tag,
    value: tag.name,
  }));

  return [{ id: 0, name: "tag.allCourses", value: "all" }, ...transformed];
};

export const scrollToElement = (triggerRef: any) => {
  triggerRef.current?.scrollIntoView({ behavior: "smooth" });
};

export const scrollToElementById = (id: string, offset = 100) => {
  const element = document.getElementById(id);
  if (element) {
    const topPosition =
      element.getBoundingClientRect().top + window.pageYOffset - offset;
    window.scrollTo({
      top: topPosition,
      behavior: "smooth",
    });
  }
};

export const keepFirstTwoWithInsert = (initialStr: string) => {
  const parts = initialStr.split(" ");
  if (parts.length < 2) return initialStr;
  const secondWord = parts[1].endsWith(":") ? parts[1].slice(0, -1) : parts[1];

  return `${parts[0]} ${t("landing.online")} ${secondWord}`;
};

export const getPricesData = (landing: any, isWebinar?: boolean) => ({
  old_price: landing?.old_price
    ? `${!isWebinar ? landing?.old_price : 49}`
    : "",
  new_price: landing?.new_price ? `${!isWebinar ? landing?.new_price : 1}` : "",
});

export const calculateDiscount = (oldPrice: number, newPrice: number) => {
  return Math.round(((oldPrice - newPrice) / oldPrice) * 100);
};

export const getDiscountPercent = (
  oldPrice: number,
  newPrice: number,
): number => {
  if (!oldPrice || oldPrice <= 0 || newPrice >= oldPrice) return 0;
  const discount = ((oldPrice - newPrice) / oldPrice) * 100;
  return Math.round(discount);
};

export const capitalizeText = (text: string) => {
  return text
    .split(" ")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(" ");
};

export const normalizeCourse = (course: any) => {
  return {
    ...course,
    sections: course.sections.map((sectionObj: any) => {
      const sectionId = Object.keys(sectionObj)[0];
      return {
        id: Number(sectionId),
        section_name: sectionObj[sectionId].section_name,
        lessons: sectionObj[sectionId].lessons.map(
          (lesson: any, index: number) => ({
            id: index + 1,
            lesson_name: lesson.lesson_name,
            video_link: lesson.video_link,
            preview: lesson.preview,
          }),
        ),
      };
    }),
  };
};

export const denormalizeCourse = (course: any) => {
  return {
    ...course,
    sections: course.sections.map((section: any) => ({
      [section.id]: {
        section_name: section.section_name,
        lessons: section.lessons.map((lesson: any) => {
          const { id, ...rest } = lesson;
          return rest;
        }),
      },
    })),
  };
};

export const normalizeLessons = (lessons: any[]): any[] => {
  return lessons.map((lessonObj, index) => {
    const key = Object.keys(lessonObj)[0];
    const lesson = lessonObj[key];

    return {
      id: index + 1,
      program: lesson.program || "",
      link: lesson.link || "",
      duration: lesson.duration || "",
      name: lesson.name || "",
      lecturer: lesson.lecturer || "",
      preview: lesson.preview || "",
    };
  });
};

export const denormalizeLessons = (lessons: any) => {
  return lessons.map((lesson: any, index: number) => {
    return {
      [`lesson${index + 1}`]: {
        link: lesson.link || "",
        name: lesson.name || "",
        program: lesson.program || "",
        duration: lesson.duration || "",
        lecturer: lesson.lecturer || "",
      },
    };
  });
};

export const isPromotionLanding = (pathname: string): boolean => {
  return (
    pathname === PATHS.LANDING.clearPattern ||
    pathname.startsWith(`${PATHS.LANDING.clearPattern}/`) ||
    pathname === PATHS.BOOK_LANDING.clearPattern ||
    pathname.startsWith(`${PATHS.BOOK_LANDING.clearPattern}/`)
  );
};

export const isVideoLanding = (pathname: string): boolean => {
  return (
    pathname === PATHS.LANDING.clearPattern || pathname.includes("/video/")
  );
};

export const isBookLanding = (pathname: string): boolean => {
  return pathname.includes(PATHS.BOOK_LANDING.clearPattern);
};

// export const isBookLandingPromotion = (pathname: string): boolean => {
//   return (
//     pathname.includes(PATHS.BOOK_LANDING.clearPattern) &&
//     !pathname.includes(PATHS.BOOK_LANDING_CLIENT.clearPattern) &&
//     !pathname.includes(PATHS.BOOKS_LISTING) &&
//     !pathname.includes(PATHS.ADMIN_BOOK_DETAIL.clearPattern) &&
//     !pathname.includes(PATHS.ADMIN_BOOK_LANDING_DETAIL.clearPattern) &&
//     !pathname.includes(PATHS.ADMIN_BOOK_LANDINGS_LISTING) &&
//     !pathname.includes(PATHS.ADMIN_BOOKS_LISTING) &&
//     !pathname.includes(PATHS.ADMIN_BOOK_LANDING_ANALYTICS.pattern)
//   );
// }; //TODO ТУТ БУДУТ БАГИ

export const formatIsoToLocalDatetime = (
  isoString: string,
  showTime?: boolean,
): string => {
  const date = new Date(isoString);

  const pad = (n: number): string => n.toString().padStart(2, "0");

  const day = pad(date.getDate());
  const month = pad(date.getMonth() + 1);
  const year = date.getFullYear();
  const hours = pad(date.getHours());
  const minutes = pad(date.getMinutes());

  const timeStr = `${hours}:${minutes}`;

  return `${showTime ? timeStr : ""} ${day}.${month}.${year}`;
};

export const getFormattedDate = (date: Date) => {
  return date.toISOString().split("T")[0];
};

export const formatShortDate = (isoDate: string) => {
  const date = new Date(isoDate);
  return date.toLocaleDateString("en-US", {
    day: "2-digit",
    month: "short",
  });
};

export const transformIdNameArrToValueNameArr = (
  arr: { id: number; name: string }[],
  addAllParam?: boolean,
) => {
  return [
    addAllParam && { value: "all", name: "All" },
    ...arr.map((item) => ({
      value: item.id,
      name: item.name,
    })),
  ];
};

export const getBasePath = (pathname: string) => {
  const trimmed = pathname.replace(/\/$/, "");
  const segments = trimmed.split("/").filter(Boolean);

  if (segments.length === 1) {
    return `/${segments[0]}`;
  }

  return `/${segments.slice(0, -1).join("/")}`;
};

export const getPaymentSource = (isOffer: boolean) => {
  const pathname = location.pathname.startsWith("/")
    ? location.pathname
    : "/" + location.pathname;

  const sources = PAYMENT_SOURCES.filter((s) => {
    const isCorrectType = isOffer
      ? s.name.endsWith("_OFFER")
      : !s.name.endsWith("_OFFER");
    return isCorrectType && s.path && pathname.startsWith(s.path);
  });

  const sorted = sources.sort((a, b) => b.path.length - a.path.length);
  return sorted[0]?.name || PAGE_SOURCES.other;
};

export const getPaymentType = (
  isFree?: boolean,
  isOffer?: boolean,
  isWebinar?: boolean,
): keyof typeof PAYMENT_TYPES | undefined => {
  if (isFree) return PAYMENT_TYPES.free;
  if (isOffer) return PAYMENT_TYPES.offer;
  if (isWebinar) return PAYMENT_TYPES.webinar;
  return undefined;
};

export const rewriteStorageLinkToCDN = (link: string) => {
  return link.replace(/^https:\/\/[^/]+\.s3\.twcstorage\.ru/, CDN_ORIGIN);
};

/**
 * Опционально переводит ссылки с публичного хоста (VITE_CDN_URL) на альтернативный (VITE_MEDIA_URL),
 * если в проекте используется отдельный домен для тяжёлых файлов (DNS-only).
 */
export const rewriteCdnLinkToMedia = (link: string) => {
  const mediaOrigin = (import.meta as any)?.env?.VITE_MEDIA_URL as string | undefined;
  if (!mediaOrigin) return link;
  try {
    const urlFromMaybeOrigin = (raw: string): URL | null => {
      const v = String(raw || "").trim();
      if (!v) return null;
      try {
        return new URL(v);
      } catch {
        // ignore
      }
      try {
        if (v.startsWith("//")) return new URL(`https:${v}`);
      } catch {
        // ignore
      }
      try {
        return new URL(`https://${v.replace(/^https?:\/\//i, "")}`);
      } catch {
        return null;
      }
    };

    const u = new URL(link);
    const cdn = CDN_ORIGIN ? urlFromMaybeOrigin(CDN_ORIGIN) : null;
    const media = urlFromMaybeOrigin(mediaOrigin);
    if (!cdn || !media) return link;
    if (cdn.hostname && u.hostname === cdn.hostname) {
      u.protocol = media.protocol;
      u.host = media.host;
      return u.toString();
    }
    return link;
  } catch {
    return link;
  }
};

export const arraysEqual = (a?: any[] | null, b?: any[] | null) => {
  if (!Array.isArray(a) || !Array.isArray(b)) return false;
  if (a.length !== b.length) return false;
  return a.every((val, i) => val === b[i]);
};

export const mapCourseToResultLanding = (course: any): ResultLandingData => {
  return {
    id: course.id,
    landing_name: course.landing_name,
    new_price: Number(course.new_price) || 0,
    old_price: Number(course.old_price) || 0,
    preview_photo: course.main_image || "",
    page_name: course.slug || "",
    authors: course.authors || [],
    course_ids: course.course_ids || [],
    language: "",
  };
};

export const formatLanguage = (
  language: "EN" | "RU" | "ES" | "AR" | "PT" | "IT",
) => {
  const result = LANGUAGES.find((obj) => obj.value === language);
  return result?.label;
};

export const getFbc = (): string | null => {
  const urlParams = new URLSearchParams(window.location.search);
  const fbclid = urlParams.get("fbclid");
  if (!fbclid) return null;
  return `fb.1.${Date.now()}.${fbclid}`;
};

export const getFbp = (): string | null => {
  const match = document.cookie.match(/_fbp=([^;]+)/);
  return match ? match[1] : null;
};

export const getCamelCaseString = (string: string): string => {
  return string.split("_").reduce((result, value, index) => {
    return index === 0
      ? result + value.toLowerCase()
      : result + capitalizeText(value);
  }, "");
};
