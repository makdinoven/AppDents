import s from "./ProfileSidebar.module.scss";
import { adminPanelTab, pagesTabs, subPagesTabs } from "../model/tabs.tsx";
import { SidebarShell } from "@/shared/components/ui/sidebar-shell/SidebarShell.tsx";
import { useSelector } from "react-redux";
import { AppRootStateType } from "@/shared/store/store.ts";
import { LogOutBtn } from "@/features/log-out";
import { UserProfileInfo } from "@/features/user-profile-info";
import { ArrowX, BurgerMenuIcon } from "@/shared/assets/icons";
import { useScreenWidth } from "@/shared/common/hooks/useScreenWidth.ts";
import { useState } from "react";

export const ProfileSidebar = () => {
  const role = useSelector((state: AppRootStateType) => state.user.role);
  const screenWidth = useScreenWidth();
  const isMobile = screenWidth < 576;
  const [isOpen, setIsOpen] = useState(false);

  const handleSidebarClose = () => {
    setIsOpen((prev) => !prev);
  };

  return (
    <div className={s.profile_sidebar_wrapper}>
      {isOpen ? (
        <ArrowX className={s.close_menu_icon} onClick={handleSidebarClose} />
      ) : (
        <BurgerMenuIcon
          className={s.burger_menu_icon}
          onClick={handleSidebarClose}
        />
      )}
      <div className={s.profile_sidebar_content}>
        <div className={`${s.profile_sidebar} ${isOpen ? s.open : ""}`}>
          <UserProfileInfo />
          <SidebarShell
            data={
              role === "admin" ? [adminPanelTab, ...subPagesTabs] : subPagesTabs
            }
            onClick={handleSidebarClose}
          />
          <SidebarShell data={pagesTabs} />
          <div className={s.logout_wrapper}>
            <LogOutBtn />
          </div>
        </div>
      </div>
    </div>
  );
};
