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
import { SidebarShellData } from "@/shared/ui/sidebar";

export const adminPanelTab: SidebarShellData = {
  type: "link",
  path: PATHS.ADMIN_LANDINGS_LISTING,
  title: "Admin panel",
  icon: <AdminIcon />,
};

export const subPagesTabs: SidebarShellData[] = [
  {
    type: "link",
    path: PATHS.PROFILE,
    title: "profile.main",
    icon: <UserStrokeIcon />,
  },
  {
    type: "link",
    path: PATHS.PROFILE_MY_COURSES,
    title: "profile.yourCourses",
    icon: <CoursesIcon />,
  },
  {
    type: "link",
    path: PATHS.PROFILE_MY_BOOKS,
    title: "profile.yourBooks",
    icon: <BooksIcon />,
  },
  {
    type: "link",
    path: PATHS.PROFILE_PURCHASE_HISTORY,
    title: "profile.purchaseHistory.purchases",
    icon: <HistoryList />,
  },
  {
    type: "link",
    path: PATHS.PROFILE_INVITED_USERS,
    title: "profile.purchaseHistory.invitedUsers",
    icon: <UserPlusIcon />,
  },
];
export const pagesTabs: SidebarShellData[] = [
  {
    type: "link",
    path: PATHS.SUPPORT,
    title: "support.supportCenter",
    icon: <Support />,
  },
  {
    type: "link",
    path: PATHS.NOTIFICATIONS,
    title: "notifications.notifications",
    icon: <NotificationIcon />,
  },
  {
    type: "link",
    path: PATHS.PROFILE_SETTINGS,
    title: "profile.settings",
    icon: <SettingsIcon />,
  },
];
