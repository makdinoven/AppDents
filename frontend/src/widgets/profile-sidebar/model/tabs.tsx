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
import { SidebarData } from "@/shared/common/types/commonTypes.ts";

export const adminPanelTab: SidebarData = {
  path: PATHS.ADMIN_LANDINGS_LISTING,
  title: "Admin panel",
  icon: <AdminIcon />,
};

export const subPagesTabs: SidebarData[] = [
  { path: PATHS.PROFILE, title: "profile.main", icon: <UserStrokeIcon /> },
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
export const pagesTabs: SidebarData[] = [
  {
    path: PATHS.PROFILE_SUPPORT,
    title: "support.supportCenter",
    icon: <Support />,
  },
  {
    path: PATHS.PROFILE_NOTIFICATIONS,
    title: "notifications.notifications",
    icon: <NotificationIcon />,
  },
  {
    path: PATHS.PROFILE_SETTINGS,
    title: "profile.settings",
    icon: <SettingsIcon />,
  },
];
