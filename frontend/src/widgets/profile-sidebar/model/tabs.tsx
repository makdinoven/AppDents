import { PATHS } from "@/app/routes/routes.ts";
import {
  AdminIcon,
  BooksIcon,
  CoursesIcon,
  HistoryList,
  NotificationIcon,
  SettingsIcon,
  Support,
  UserPlusIcon,
  UserStrokeIcon,
} from "@/shared/assets/icons";
// import type { SidebarShellData } from "@/shared/ui/sidebar";

export const adminPanelTab = {
  path: PATHS.ADMIN_LANDINGS_LISTING,
  title: "Admin panel",
  icon: <AdminIcon />,
};

export const subPagesTabs = [
  {
    path: PATHS.PROFILE,
    title: "profile.main",
    icon: <UserStrokeIcon />,
  },
  {
    path: PATHS.PROFILE_MY_COURSES,
    title: "profile.yourCourses",
    icon: <CoursesIcon />,
  },
  {
    path: PATHS.PROFILE_MY_BOOKS,
    title: "profile.yourBooks",
    icon: <BooksIcon />,
  },
  {
    path: PATHS.PROFILE_PURCHASE_HISTORY,
    title: "profile.purchaseHistory.purchases",
    icon: <HistoryList />,
  },
  {
    path: PATHS.PROFILE_INVITED_USERS,
    title: "profile.purchaseHistory.invitedUsers",
    icon: <UserPlusIcon />,
  },
];
export const pagesTabs = [
  {
    path: PATHS.SUPPORT,
    title: "support.supportCenter",
    icon: <Support />,
  },
  {
    path: PATHS.NOTIFICATIONS,
    title: "notifications.notifications",
    icon: <NotificationIcon />,
  },
  {
    path: PATHS.PROFILE_SETTINGS,
    title: "profile.settings",
    icon: <SettingsIcon />,
  },
];
