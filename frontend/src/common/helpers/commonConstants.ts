import { Path } from "../../routes/routes.ts";
import {
  CartIcon,
  CoursesIcon,
  HomeIcon,
  ProfessorsIcon,
} from "../../assets/logos/index";

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
  { icon: HomeIcon, text: "nav.home", link: Path.main },
  // { icon: BooksIcon, text: "nav.books", link: "Path.books" },
  { icon: ProfessorsIcon, text: "nav.professors", link: Path.professors },
  { icon: CoursesIcon, text: "nav.courses", link: Path.courses },
  { icon: CartIcon, text: "nav.cart", link: Path.cart },
];

export const AUTH_MODAL_ROUTES = [Path.login, Path.signUp, Path.passwordReset];

export const LANDING_ROUTES = [
  Path.landing,
  Path.landingClient,
  Path.freeLanding,
  Path.freeLandingClient,
  Path.videoLanding,
  Path.webinarLanding,
];

export const LANDING_AD_ROUTES = [
  Path.landing,
  Path.freeLanding,
  Path.videoLanding,
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

export const OPEN_SEARCH_KEY = "GS";

export const PAYMENT_PAGE_KEY = "BUY";

export const BASE_URL = "https://dent-s.com";

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

export const PAGE_SOURCES = {
  main: "HOMEPAGE",
  cart: "CART",
  landing: "LANDING",
  landingOffer: "LANDING_OFFER",
  videoLanding: "LANDING_VIDEO",
  webinarLanding: "LANDING_WEBINAR",
  professor: "PROFESSOR_PAGE",
  professorOffer: "PROFESSOR_OFFER",
  professorListOffer: "PROF_LIST_OFFER",
  cabinetOffer: "CABINET_OFFER",
  cabinetFree: "CABINET_FREE",
  courses: "COURSES_PAGE",
  coursesOffer: "COURSES_OFFER",
  specialOffer: "SPECIAL_OFFER",
  other: "OTHER",
} as const;

export const PAYMENT_SOURCES = [
  { name: PAGE_SOURCES.main, path: Path.main },
  { name: PAGE_SOURCES.cart, path: Path.cart },
  { name: PAGE_SOURCES.landing, path: `/${Path.landingClient}` },
  { name: PAGE_SOURCES.landing, path: Path.landing },
  { name: PAGE_SOURCES.videoLanding, path: Path.videoLanding },
  { name: PAGE_SOURCES.webinarLanding, path: Path.webinarLanding },
  { name: PAGE_SOURCES.professor, path: Path.professor },
  { name: PAGE_SOURCES.professorOffer, path: Path.professor },
  { name: PAGE_SOURCES.professorListOffer, path: Path.professors },
  { name: PAGE_SOURCES.cabinetOffer, path: Path.profile },
  { name: PAGE_SOURCES.cabinetFree, path: `${Path.profile}/${Path.myCourse}` },
  { name: PAGE_SOURCES.landingOffer, path: Path.landing },
  { name: PAGE_SOURCES.landingOffer, path: `/${Path.landingClient}` },
  // { name: "VIDEO_LANDING", path: `/${Path.videoLanding}` },
  // {name: "SPECIAL_OFFER", path: `/${Path.profile}` },
  { name: PAGE_SOURCES.courses, path: Path.courses },
  { name: PAGE_SOURCES.coursesOffer, path: Path.courses },
];

export const REF_CODE_PARAM = "rc";

export const REF_CODE_LS_KEY = "DENTS_RC";

export const LS_LANGUAGE_KEY = "DENTS_LANGUAGE";

export const LS_TOKEN_KEY = "access_token";

export const LS_REF_LINK_KEY = "DENTS_REF_LINK";
