import s from "./ProfileSidebar.module.scss";
import { adminPanelTab, pagesTabs, subPagesTabs } from "../model/tabs.tsx";
import { SidebarShell } from "@/shared/components/ui/sidebar-shell/SidebarShell.tsx";
import { useSelector } from "react-redux";
import { AppRootStateType } from "@/shared/store/store.ts";
import { LogOutBtn } from "@/features/log-out";
import { UserProfileInfo } from "@/features/user-profile-info";
import { ArrowX, BurgerMenuIcon } from "@/shared/assets/icons";
import { useRef, useState } from "react";
import useOutsideClick from "@/shared/common/hooks/useOutsideClick.ts";

export const ProfileSidebar = () => {
  const role = useSelector((state: AppRootStateType) => state.user.role);
  const [isOpen, setIsOpen] = useState(false);
  const sidebarRef = useRef<HTMLDivElement>(null);

  const handleSidebarClose = () => {
    setIsOpen(false);
  };
  const handleSidebarOpen = () => {
    setIsOpen(true);
  };

  useOutsideClick(sidebarRef, handleSidebarClose);

  return (
    <div className={s.profile_sidebar_wrapper}>
      {isOpen ? (
        <ArrowX className={s.close_menu_icon} onClick={handleSidebarClose} />
      ) : (
        <BurgerMenuIcon
          className={s.burger_menu_icon}
          onClick={handleSidebarOpen}
        />
      )}
      <div className={s.profile_sidebar_content}>
        <div
          className={`${s.profile_sidebar} ${isOpen ? s.open : ""}`}
          ref={sidebarRef}
        >
          <UserProfileInfo />
          <SidebarShell
            data={
              role === "admin" ? [adminPanelTab, ...subPagesTabs] : subPagesTabs
            }
            onClick={handleSidebarClose}
          />
          <SidebarShell data={pagesTabs} onClick={handleSidebarClose} />
          <div className={s.logout_wrapper}>
            <LogOutBtn />
          </div>
        </div>
      </div>
    </div>
  );
};
