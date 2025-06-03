import { Path } from "../../routes/routes.ts";
import { CartIcon, HomeIcon, ProfessorsIcon } from "../../assets/logos/index";

export const LANGUAGES = [
  { label: "English", value: "EN" },
  { label: "Русский", value: "RU" },
  { label: "Español", value: "ES" },
  { label: "العربية", value: "AR" },
  { label: "Português", value: "PT" },
  { label: "Italiano", value: "IT" },
];

export const NAV_BUTTONS = [
  { icon: HomeIcon, text: "nav.home", link: Path.main },
  // { icon: CoursesIcon, text: "nav.courses", link: Path.courses },
  // { icon: BooksIcon, text: "nav.books", link: "Path.books" },
  { icon: ProfessorsIcon, text: "nav.professors", link: Path.professors },
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

export const ANALYTICS_LIMITS = [
  { name: "10", value: "10" },
  { name: "20", value: "20" },
  { name: "50", value: "50" },
  { name: "100", value: "100" },
  { name: "200", value: "200" },
  { name: "500", value: "500" },
];

export const REF_CODE_PARAM = "rc";

export const REF_CODE_LS_KEY = "DENTS_RC";
