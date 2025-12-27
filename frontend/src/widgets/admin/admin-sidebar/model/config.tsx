import { PATHS } from "@/app/routes/routes";
import {
  ArrowUpDown,
  BookLucide,
  BooksIcon,
  CoinOff,
  CoursesIcon,
  DollarLucide,
  FileIcon,
  LanguageIcon,
  MegaphoneIcon,
  PlayIconOutlined,
  ProfessorsIcon,
  Scissors,
  SearchIcon,
  ShareIcon,
  UserPlusIcon,
  UsersIcon,
  UserStar,
  UserStrokeIcon,
} from "@/shared/assets/icons";

export const ADMIN_SIDEBAR_SECTIONS = [
  {
    title: "CONTENT",
    items: [
      {
        path: PATHS.ADMIN_LANDINGS_LISTING,
        title: "admin.landings.landings",
        icon: <CoursesIcon />,
      },
      {
        path: PATHS.ADMIN_COURSES_LISTING,
        title: "admin.courses.courses",
        icon: <PlayIconOutlined />,
      },
      {
        path: PATHS.ADMIN_AUTHORS_LISTING,
        title: "admin.authors.authors",
        icon: <ProfessorsIcon />,
      },

      {
        path: PATHS.ADMIN_USERS_LISTING,
        title: "admin.users.users",
        icon: <UserStrokeIcon />,
      },
      {
        path: PATHS.ADMIN_BOOKS_LISTING,
        title: "admin.books.books",
        icon: <BookLucide />,
      },
      {
        path: PATHS.ADMIN_BOOK_LANDINGS_LISTING,
        title: "admin.bookLandings.bookLandings",
        icon: <BooksIcon />,
      },
    ],
  },

  {
    title: "ANALYTICS",
    items: [
      {
        path: PATHS.ADMIN_ANALYTICS_PURCHASES,
        title: "admin.analytics.purchases",
        icon: <DollarLucide />,
      },
      {
        path: PATHS.ADMIN_ANALYTICS_LANG_STATS,
        title: "admin.analytics.languageStats",
        icon: <LanguageIcon />,
      },
      {
        path: PATHS.ADMIN_ANALYTICS_AD_LISTING,
        title: "admin.analytics.adListing",
        icon: <MegaphoneIcon />,
      },
      {
        path: PATHS.ADMIN_ANALYTICS_REFERRALS,
        title: "admin.analytics.referrals",
        icon: <ShareIcon />,
      },
      {
        path: PATHS.ADMIN_ANALYTICS_USER_GROWTH,
        title: "admin.analytics.userGrowth",
        icon: <UserPlusIcon />,
      },
      {
        path: PATHS.ADMIN_ANALYTICS_FREEWEBS,
        title: "admin.analytics.freewebs",
        icon: <CoinOff />,
      },
      {
        path: PATHS.ADMIN_ANALYTICS_TRAFFIC,
        title: "admin.analytics.traffic",
        icon: <ArrowUpDown />,
      },
      {
        path: PATHS.ADMIN_ANALYTICS_SEARCH_QUERIES,
        title: "admin.analytics.searchQueries",
        icon: <SearchIcon />,
      },
    ],
  },

  {
    title: "AD CONTROL",
    items: [
      {
        path: PATHS.ADMIN_AD_CONTOL_LISTING,
        title: "admin.adControl.listing",
        icon: <MegaphoneIcon />,
      },
      {
        path: PATHS.ADMIN_AD_CONTROL_ACCOUNTS,
        title: "admin.adControl.accounts",
        icon: <UserStar />,
      },
      {
        path: PATHS.ADMIN_AD_CONTROL_STAFF,
        title: "admin.adControl.staff",
        icon: <UsersIcon />,
      },
    ],
  },

  {
    title: "TOOLS",
    items: [
      {
        path: PATHS.ADMIN_TOOLS_VIDEO_SUMMARY,
        title: "admin.tools.videoSummary.title",
        icon: <FileIcon />,
      },
      {
        path: PATHS.ADMIN_TOOLS_CLIP,
        title: "admin.tools.clip.title",
        icon: <Scissors />,
      },
      {
        path: PATHS.ADMIN_TOOLS_MAGIC,
        title: "admin.tools.magicVideoFix.title",
        icon: <PlayIconOutlined />,
      },
    ],
  },
];
