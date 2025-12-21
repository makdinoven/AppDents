import s from "./ProfileSidebar.module.scss";
import { useSelector } from "react-redux";
import { AppRootStateType } from "@/shared/store/store.ts";
import { Sidebar } from "@/shared/components/ui/sidebar";
import { UserProfileInfo } from "@/features/user-profile-info";
import { LogOutBtn } from "@/features/log-out";
import {
  adminPanelTab,
  pagesTabs,
  subPagesTabs,
} from "@/widgets/profile-sidebar/model/tabs.tsx";

export const ProfileSidebar = () => {
  const role = useSelector((state: AppRootStateType) => state.user.role);
  const subPages =
    role === "admin" ? [adminPanelTab, ...subPagesTabs] : subPagesTabs;
  const profileSidebarData = [subPages, pagesTabs];

  return (
    <Sidebar
      menuButtonText="profile.menu"
      menuButtonClassName={s.menu_button}
      sidebarShellsData={profileSidebarData}
      topSlot={<UserProfileInfo />}
      bottomSlot={
        <div className={s.logout_wrapper}>
          <LogOutBtn />
        </div>
      }
    />
  );
};
