import { Path } from "../../routes/routes.ts";

export const LANGUAGES = [
  { label: "English", value: "EN" },
  { label: "Русский", value: "RU" },
  { label: "Español", value: "ES" },
  { label: "العربية", value: "AR" },
  { label: "Português", value: "PT" },
  { label: "Italiano", value: "IT" },
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

export const BASE_URL = "https://dent-s.com";

export const SORT_FILTERS = [
  { name: "tag.common.popular", value: "popular" },
  { name: "tag.common.bestPrices", value: "discount" },
  { name: "tag.common.new", value: "new" },
];
