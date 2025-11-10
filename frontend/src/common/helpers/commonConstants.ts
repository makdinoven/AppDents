import { Path } from "../../routes/routes.ts";
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
} from "../../assets/icons/index.ts";
import { LanguagesType } from "../../components/ui/LangLogo/LangLogo.tsx";

export const BASE_URL = import.meta.env.VITE_API_BASE_URL;

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
  { icon: CoursesIcon, text: "nav.courses", link: Path.courses },
  { icon: BooksIcon, text: "nav.books", link: Path.books },
  { icon: ProfessorsIcon, text: "nav.professors", link: Path.professors },
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

export const BOOK_LANDING_ROUTES = [Path.bookLanding, Path.bookLandingClient];

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
  { name: PAGE_SOURCES.main, path: Path.main },
  { name: PAGE_SOURCES.cart, path: Path.cart },
  { name: PAGE_SOURCES.landing, path: `/${Path.landingClient}` },
  { name: PAGE_SOURCES.landing, path: Path.landing },
  { name: PAGE_SOURCES.videoLanding, path: Path.videoLanding },
  { name: PAGE_SOURCES.webinarLanding, path: Path.webinarLanding },
  { name: PAGE_SOURCES.professor, path: Path.professor },
  { name: PAGE_SOURCES.professorOffer, path: Path.professor },
  { name: PAGE_SOURCES.professorListOffer, path: Path.professors },
  { name: PAGE_SOURCES.cabinetOffer, path: Path.profileMain },
  {
    name: PAGE_SOURCES.cabinetFree,
    path: `${Path.profileMain}/${Path.myCourse}`,
  },
  { name: PAGE_SOURCES.landingOffer, path: Path.landing },
  { name: PAGE_SOURCES.landingOffer, path: `/${Path.landingClient}` },
  { name: PAGE_SOURCES.courses, path: Path.courses },
  { name: PAGE_SOURCES.coursesOffer, path: Path.courses },
  { name: PAGE_SOURCES.books, path: Path.books },
  { name: PAGE_SOURCES.booksOffer, path: Path.books },
  { name: PAGE_SOURCES.booksLanding, path: Path.bookLandingClient },
  { name: PAGE_SOURCES.booksLanding, path: Path.bookLanding },
  { name: PAGE_SOURCES.booksLandingOffer, path: Path.bookLandingClient },
  { name: PAGE_SOURCES.booksLandingOffer, path: Path.bookLanding },
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

export const ADMIN_SIDEBAR_LINKS = [
  {
    label: "admin.content",
    innerLinks: [
      { label: "admin.landings.landings", link: Path.adminLandingListing },
      { label: "admin.courses.courses", link: Path.adminCourseListing },
      { label: "admin.authors.authors", link: Path.adminAuthorListing },
      { label: "admin.users.users", link: Path.adminUserListing },
      { label: "admin.books.books", link: Path.adminBookListing },
      {
        label: "admin.bookLandings.bookLandings",
        link: Path.adminBookLandingListing,
      },
    ],
  },
  {
    label: "admin.analytics.analytics",
    innerLinks: [
      { label: "admin.analytics.purchases", link: Path.adminPurchases },
      {
        label: "admin.analytics.languageCoursesStats",
        link: Path.adminCoursesLanguageStats,
      },
      {
        label: "admin.analytics.languageBooksStats",
        link: Path.adminBooksLanguageStats,
      },
      { label: "admin.analytics.adListing", link: Path.adminAdListing },
      { label: "admin.analytics.referrals", link: Path.adminReferrals },
      { label: "admin.analytics.userGrowth", link: Path.adminUserGrowth },
      { label: "admin.analytics.freewebs", link: Path.adminFreewebs },
      { label: "admin.analytics.traffic", link: Path.adminTraffic },
    ],
  },
  {
    label: "admin.adControl.adControl",
    innerLinks: [
      { label: "admin.adControl.listing", link: Path.adminAdControlListing },
      { label: "admin.adControl.accounts", link: Path.adminAdControlAccounts },
      { label: "admin.adControl.staff", link: Path.adminAdControlStaff },
    ],
  },
  {
    label: "admin.tools.tools",
    innerLinks: [
      { label: "Video summary", link: Path.adminVideoSummaryTool },
      { label: "Clip tool", link: Path.adminClipTool },
      { label: "Magic video fix", link: Path.adminMagicVideoTool },
    ],
  },
];
