const ADMIN_PREFIX = "/admin";

export const PATHS = {
  MAIN: "/",
  LOGIN: "/login",
  PASSWORD_RESET: "/password-reset",
  SEARCH: "/search",
  CART: "/cart",
  COURSES_LISTING: "/courses",
  COURSES_LISTING_FREE: "/courses/free",
  BOOKS_LISTING: "/books",
  SIGN_UP: "/sign-up",
  PAYMENT: "/buy",
  SUCCESS_PAYMENT: "/payment-success",

  PROFILE: "/profile-main",
  PROFILE_PURCHASE_HISTORY: "/purchase-history",
  PROFILE_INVITED_USERS: "/invited-users",
  PROFILE_MY_COURSES: "/my-courses",
  PROFILE_MY_BOOKS: "/my-books",
  PROFILE_SETTINGS: "/settings",
  PROFILE_SUPPORT: "/support",
  PROFILE_NOTIFICATIONS: "/notifications",
  PROFILE_SUPPORT_CHAT: {
    clearPattern: "/support/c",
    pattern: "/support/c/:id",
    build: (id: string) => `/support/c/${id}`,
  },
  PROFILE_MY_COURSE: {
    clearPattern: "/my-course",
    pattern: "/my-course/:id",
    build: (id: string) => `/my-course/${id}`,
  },
  PROFILE_MY_BOOK: {
    clearPattern: "/my-book",
    pattern: "/my-book/:id",
    build: (id: string) => `/my-book/${id}`,
  },
  PROFILE_COURSE_LESSON: {
    pattern: "lesson/:sectionId/:lessonId",
    build: (sectionId: string, lessonId: string) =>
      `lesson/${sectionId}/${lessonId}`,
  },

  PROFESSOR_PAGE: {
    clearPattern: "/professor",
    pattern: "/professor/:id",
    build: (id: string) => `/professor/${id}`,
  },
  PROFESSORS_LISTING: "/professors",

  INFO: {
    pattern: "/info/:pageType",
    build: (pageType: string) => `/info/${pageType}`,
  },
  INFO_PRIVACY: "/info/privacy-policy",
  INFO_COOKIES: "/info/cookie-policy",
  INFO_TERMS: "/info/terms-of-use",

  LANDING: {
    clearPattern: "/course",
    pattern: "/course/:slug",
    build: (slug: string) => `/course/${slug}`,
  },
  LANDING_VIDEO: {
    clearPattern: "/course/video",
    pattern: "/course/video/:slug",
    build: (slug: string) => `/course/video/${slug}`,
  },
  LANDING_WEBINAR: {
    clearPattern: "/course/webinar",
    pattern: "/course/webinar/:slug",
    build: (slug: string) => `/course/webinar/${slug}`,
  },
  LANDING_FREE: {
    clearPattern: "/course/free",
    pattern: "/course/free/:slug",
    build: (slug: string) => `/course/free/${slug}`,
  },
  LANDING_CLIENT: {
    clearPattern: "/client/course",
    pattern: "/client/course/:slug",
    build: (slug: string) => `/client/course/${slug}`,
  },
  LANDING_CLIENT_FREE: {
    clearPattern: "/client/course/free",
    pattern: "/client/course/free/:slug",
    build: (slug: string) => `/client/course/free/${slug}`,
  },

  BOOK_LANDING: {
    clearPattern: "/book",
    pattern: "/book/:slug",
    build: (slug: string) => `/book/${slug}`,
  },
  BOOK_LANDING_CLIENT: {
    clearPattern: "/client/book",
    pattern: "/client/book/:slug",
    build: (slug: string) => `/client/book/${slug}`,
  },

  ADMIN: ADMIN_PREFIX,

  ADMIN_COURSE_DETAIL: {
    clearPattern: `${ADMIN_PREFIX}/detail/course`,
    pattern: `${ADMIN_PREFIX}/detail/course/:id`,
    build: (id: string) => `${ADMIN_PREFIX}/detail/course/${id}`,
  },
  ADMIN_LANDING_DETAIL: {
    clearPattern: `${ADMIN_PREFIX}/detail/landing`,
    pattern: `${ADMIN_PREFIX}/detail/landing/:id`,
    build: (id: string) => `${ADMIN_PREFIX}/detail/landing/${id}`,
  },
  ADMIN_USER_DETAIL: {
    clearPattern: `${ADMIN_PREFIX}/detail/user`,
    pattern: `${ADMIN_PREFIX}/detail/user/:id`,
    build: (id: string) => `${ADMIN_PREFIX}/detail/user/${id}`,
  },
  ADMIN_AUTHOR_DETAIL: {
    clearPattern: `${ADMIN_PREFIX}/detail/author`,
    pattern: `${ADMIN_PREFIX}/detail/author/:id`,
    build: (id: string) => `${ADMIN_PREFIX}/detail/author/${id}`,
  },
  ADMIN_BOOK_DETAIL: {
    clearPattern: `${ADMIN_PREFIX}/detail/book`,
    pattern: `${ADMIN_PREFIX}/detail/book/:id`,
    build: (id: string) => `${ADMIN_PREFIX}/detail/book/${id}`,
  },
  ADMIN_BOOK_LANDING_DETAIL: {
    clearPattern: `${ADMIN_PREFIX}/detail/book-landing`,
    pattern: `${ADMIN_PREFIX}/detail/book-landing/:id`,
    build: (id: string) => `${ADMIN_PREFIX}/detail/book-landing/${id}`,
  },

  ADMIN_LANDINGS_LISTING: `${ADMIN_PREFIX}/content/landings-listing`,
  ADMIN_COURSES_LISTING: `${ADMIN_PREFIX}/content/courses-listing`,
  ADMIN_AUTHORS_LISTING: `${ADMIN_PREFIX}/content/authors-listing`,
  ADMIN_BOOKS_LISTING: `${ADMIN_PREFIX}/content/books-listing`,
  ADMIN_USERS_LISTING: `${ADMIN_PREFIX}/content/users-listing`,
  ADMIN_BOOK_LANDINGS_LISTING: `${ADMIN_PREFIX}/content/book-landings-listing`,

  ADMIN_LANDING_ANALYTICS: {
    pattern: `${ADMIN_PREFIX}/landing-analytics/:id`,
    build: (id: string) => `${ADMIN_PREFIX}/landing-analytics/${id}`,
  },
  ADMIN_BOOK_LANDING_ANALYTICS: {
    pattern: `${ADMIN_PREFIX}/book-landing-analytics/:id`,
    build: (id: string) => `${ADMIN_PREFIX}/book-landing-analytics/${id}`,
  },

  ADMIN_ANALYTICS_PURCHASES: `${ADMIN_PREFIX}/analytics/purchases`,
  ADMIN_ANALYTICS_LANG_STATS: `${ADMIN_PREFIX}/analytics/language-stats`,
  ADMIN_ANALYTICS_AD_LISTING: `${ADMIN_PREFIX}/analytics/ad-listing`,
  ADMIN_ANALYTICS_REFERRALS: `${ADMIN_PREFIX}/analytics/referrals`,
  ADMIN_ANALYTICS_USER_GROWTH: `${ADMIN_PREFIX}/analytics/user-growth`,
  ADMIN_ANALYTICS_FREEWEBS: `${ADMIN_PREFIX}/analytics/freewebs`,
  ADMIN_ANALYTICS_TRAFFIC: `${ADMIN_PREFIX}/analytics/traffic`,
  ADMIN_ANALYTICS_SEARCH_QUERIES: `${ADMIN_PREFIX}/analytics/search-queries`,

  ADMIN_AD_CONTOL_LISTING: `${ADMIN_PREFIX}/ad-control/landings-listing`,
  ADMIN_AD_CONTROL_ACCOUNTS: `${ADMIN_PREFIX}/ad-control/ad-accounts-listing`,
  ADMIN_AD_CONTROL_STAFF: `${ADMIN_PREFIX}/ad-control/staff-listing`,

  ADMIN_TOOLS_VIDEO_SUMMARY: `${ADMIN_PREFIX}/tools/video-summary`,
  ADMIN_TOOLS_CLIP: `${ADMIN_PREFIX}/tools/clip`,
  ADMIN_TOOLS_MAGIC: `${ADMIN_PREFIX}/tools/magic-video`,
};

export const LANDING_PATHS = [
  PATHS.LANDING,
  PATHS.LANDING_CLIENT,
  PATHS.LANDING_FREE,
  PATHS.LANDING_CLIENT_FREE,
  PATHS.LANDING_VIDEO,
  PATHS.LANDING_WEBINAR,
];

export const BOOK_LANDING_PATHS = [
  PATHS.BOOK_LANDING,
  PATHS.BOOK_LANDING_CLIENT,
];
