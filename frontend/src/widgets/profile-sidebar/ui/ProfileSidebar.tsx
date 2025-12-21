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
import { RemoveScroll } from "react-remove-scroll";
import Button from "@/shared/components/ui/Button/Button.tsx";

export const ProfileSidebar = () => {
  const role = useSelector((state: AppRootStateType) => state.user.role);
  const [isOpen, setIsOpen] = useState(false);
  const sidebarRef = useRef<HTMLDivElement>(null);

  const handleSidebarClose = () => {
    setIsOpen(false);
  };
  const handleChangeSidebarState = () => {
    setIsOpen((prev) => !prev);
  };

  useOutsideClick(sidebarRef, handleSidebarClose);

  return (
    <RemoveScroll enabled={isOpen}>
      <div className={s.profile_sidebar_wrapper}>
        <Button
          iconLeft={isOpen ? <ArrowX /> : <BurgerMenuIcon />}
          onClick={handleChangeSidebarState}
          text="profile.menu"
          className={s.menu_button}
          type="button"
        />
        <div className={s.profile_sidebar_content}>
          <div
            className={`${s.profile_sidebar} ${isOpen ? s.open : ""}`}
            ref={sidebarRef}
          >
            <UserProfileInfo />
            <SidebarShell
              data={
                role === "admin"
                  ? [adminPanelTab, ...subPagesTabs]
                  : subPagesTabs
              }
              onClick={handleChangeSidebarState}
            />
            <SidebarShell data={pagesTabs} onClick={handleChangeSidebarState} />
            <div className={s.logout_wrapper}>
              <LogOutBtn />
            </div>
          </div>
        </div>
      </div>
    </RemoveScroll>
  );
};
