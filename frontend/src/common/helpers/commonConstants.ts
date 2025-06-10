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

export const BASE_URL = "https://dent-s.com";

export const SORT_FILTERS = [
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

export const PAYMENT_SOURCES = [
  { name: "HOMEPAGE", path: Path.main },
  { name: "CART", path: Path.cart },
  { name: "LANDING", path: `/${Path.landingClient}` },
  { name: "LANDING", path: Path.landing },
  { name: "PROFESSOR_PAGE", path: Path.professor },
  { name: "PROFESSOR_OFFER", path: Path.professor },
  { name: "PROF_LIST_OFFER", path: Path.professors },
  { name: "CABINET_OFFER", path: Path.profile },
  { name: "CABINET_FREE", path: `${Path.profile}/${Path.myCourse}` },
  { name: "LANDING_OFFER", path: Path.landing },
  { name: "LANDING_OFFER", path: `/${Path.landingClient}` },
  { name: "COURSES_PAGE", path: Path.courses },
  { name: "COURSES_OFFER", path: Path.courses },
];

export const REF_CODE_PARAM = "rc";

export const REF_CODE_LS_KEY = "DENTS_RC";

export const LS_LANGUAGE_KEY = "DENTS_LANGUAGE";
