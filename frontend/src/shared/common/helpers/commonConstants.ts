import { PATHS } from "../../../app/routes/routes.ts";
import {
  ArFlag,
  BooksIcon,
  CartIcon,
  CoursesIcon,
  EnFlag,
  EsFlag,
  HomeIcon,
  ItFlag,
  ProfessorsIcon,
  PtFlag,
  RuFlag,
} from "../../assets/icons";
import { LanguagesType } from "../../components/ui/LangLogo/LangLogo.tsx";
import { Brand } from "../types/commonTypes.ts";

export const BASE_URL = import.meta.env.VITE_API_BASE_URL;
export const CDN_ORIGIN = import.meta.env.VITE_CDN_URL;
export const BRAND = (import.meta.env.VITE_BRAND as Brand) || "dents";

export const LANGUAGES = [
  { label: "English", value: "EN" },
  { label: "Русский", value: "RU" },
  { label: "Español", value: "ES" },
  { label: "العربية", value: "AR" },
  { label: "Português", value: "PT" },
  { label: "Italiano", value: "IT" },
];

export const LANGUAGES_NAME = [
  { name: "All", value: "all" },
  { name: "English", value: "EN" },
  { name: "Русский", value: "RU" },
  { name: "Español", value: "ES" },
  { name: "العربية", value: "AR" },
  { name: "Português", value: "PT" },
  { name: "Italiano", value: "IT" },
];

export const NAV_BUTTONS = [
  { icon: HomeIcon, text: "nav.home", link: PATHS.MAIN },
  { icon: CoursesIcon, text: "nav.courses", link: PATHS.COURSES_LISTING },
  { icon: BooksIcon, text: "nav.books", link: PATHS.BOOKS_LISTING },
  {
    icon: ProfessorsIcon,
    text: "nav.professors",
    link: PATHS.PROFESSORS_LISTING,
  },
  { icon: CartIcon, text: "nav.cart", link: PATHS.CART },
];

export const AUTH_MODAL_ROUTES = [
  PATHS.LOGIN,
  PATHS.SIGN_UP,
  PATHS.PASSWORD_RESET,
];

export const ROLES = [
  {
    label: "Admin",
    value: "admin",
  },
  {
    label: "User",
    value: "user",
  },
];

export const INITIAL_AUTHOR = {
  name: "New author",
  description: "",
  photo: "",
};

export const INITIAL_COURSE = {
  name: "New course",
  description: "",
};

export const INITIAL_LANDING = {
  landing_name: "New landing",
  is_hidden: true,
};

export const INITIAL_USER = {
  email: "newuser@dents.com",
  password: "Newuserpassword123!",
  role: "user",
};

export const PAYMENT_PAGE_KEY = "BUY";

export const PAYMENT_TYPE_KEY = "PT";

export const PAYMENT_MODE_KEY = "PM";

export const SORT_FILTERS = [
  { name: "tag.common.rec", value: "recommend" },
  { name: "tag.common.popular", value: "popular" },
  { name: "tag.common.bestPrices", value: "discount" },
  { name: "tag.common.new", value: "new" },
];

export type FilterKeys = "tags" | "sort" | "size" | "language";

export const FILTER_PARAM_KEYS: Record<FilterKeys, string> = {
  tags: "tags",
  sort: "sort",
  size: "size",
  language: "lang",
};

export const ANALYTICS_LIMITS = [
  { name: "10", value: "10" },
  { name: "20", value: "20" },
  { name: "50", value: "50" },
  { name: "100", value: "100" },
  { name: "200", value: "200" },
  { name: "500", value: "500" },
];

export const PAGE_SIZES = [
  { name: "10", value: "10" },
  { name: "20", value: "20" },
  { name: "50", value: "50" },
  { name: "100", value: "100" },
];

export const PAGE_SIZES_ALTERNATE = [
  { name: "12", value: "12" },
  { name: "24", value: "24" },
  { name: "60", value: "60" },
  { name: "120", value: "120" },
];

export const PAGE_SOURCES = {
  main: "HOMEPAGE",
  cart: "CART",
  landing: "LANDING",
  landingOffer: "LANDING_OFFER",
  videoLanding: "VIDEO_LANDING",
  webinarLanding: "LANDING_WEBINAR",
  professor: "PROFESSOR_PAGE",
  professorOffer: "PROFESSOR_OFFER",
  professorListOffer: "PROF_LIST_OFFER",
  cabinetOffer: "CABINET_OFFER",
  cabinetFree: "CABINET_FREE",
  courses: "COURSES_PAGE",
  coursesOffer: "COURSES_OFFER",
  books: "BOOKS_PAGE",
  booksOffer: "BOOKS_OFFER",
  booksLanding: "BOOKS_LANDING",
  booksLandingOffer: "BOOKS_LANDING_OFFER",
  specialOffer: "SPECIAL_OFFER",
  other: "OTHER",
} as const;

export const PAYMENT_SOURCES = [
  { name: PAGE_SOURCES.main, path: PATHS.MAIN },
  { name: PAGE_SOURCES.cart, path: PATHS.CART },
  { name: PAGE_SOURCES.landing, path: PATHS.LANDING_CLIENT.clearPattern }, //TODO ТУТ БУДУТ БАГИ
  { name: PAGE_SOURCES.landing, path: PATHS.LANDING.clearPattern },
  { name: PAGE_SOURCES.videoLanding, path: PATHS.LANDING_VIDEO.clearPattern },
  {
    name: PAGE_SOURCES.webinarLanding,
    path: PATHS.LANDING_WEBINAR.clearPattern,
  },
  { name: PAGE_SOURCES.professor, path: PATHS.PROFESSOR_PAGE.clearPattern },
  {
    name: PAGE_SOURCES.professorOffer,
    path: PATHS.PROFESSOR_PAGE.clearPattern,
  },
  { name: PAGE_SOURCES.professorListOffer, path: PATHS.PROFESSORS_LISTING },
  { name: PAGE_SOURCES.cabinetOffer, path: PATHS.PROFILE },
  {
    name: PAGE_SOURCES.cabinetFree,
    path: PATHS.PROFILE_MY_COURSE.clearPattern, //TODO ТУТ БУДУТ БАГИ
  },
  { name: PAGE_SOURCES.landingOffer, path: PATHS.LANDING.clearPattern },
  { name: PAGE_SOURCES.landingOffer, path: PATHS.LANDING_CLIENT.clearPattern },
  { name: PAGE_SOURCES.courses, path: PATHS.COURSES_LISTING },
  { name: PAGE_SOURCES.coursesOffer, path: PATHS.COURSES_LISTING },
  { name: PAGE_SOURCES.books, path: PATHS.BOOKS_LISTING },
  { name: PAGE_SOURCES.booksOffer, path: PATHS.BOOKS_LISTING },
  {
    name: PAGE_SOURCES.booksLanding,
    path: PATHS.BOOK_LANDING_CLIENT.clearPattern,
  },
  { name: PAGE_SOURCES.booksLanding, path: PATHS.BOOK_LANDING.clearPattern },
  {
    name: PAGE_SOURCES.booksLandingOffer,
    path: PATHS.BOOK_LANDING_CLIENT.clearPattern,
  },
  {
    name: PAGE_SOURCES.booksLandingOffer,
    path: PATHS.BOOK_LANDING.clearPattern,
  },
];

export const PAYMENT_TYPES = {
  free: "free",
  offer: "offer",
  webinar: "webinar",
} as const;

export const PAYMENT_SOURCES_OPTIONS = [
  { value: "ALL", label: "ALL" },
  ...Array.from(
    new Map(
      PAYMENT_SOURCES.map((item) => [
        item.name,
        { value: item.name, label: item.name },
      ]),
    ).values(),
  ),
  { value: "SPECIAL_OFFER", label: "SPECIAL_OFFER" },
];

export const REF_CODE_PARAM = "rc";

export const REF_CODE_LS_KEY = "DENTS_RC";

export const LS_LANGUAGE_KEY = "DENTS_LANGUAGE";

export const LS_TOKEN_KEY = "access_token";

export const LS_REF_LINK_KEY = "DENTS_REF_LINK";

export const BOOK_FORMATS = ["PDF", "EPUB", "MOBI", "AZW3", "FB2"];

export const LANGUAGE_FLAGS: Record<LanguagesType, React.FC> = {
  EN: EnFlag,
  ES: EsFlag,
  PT: PtFlag,
  AR: ArFlag,
  IT: ItFlag,
  RU: RuFlag,
};
