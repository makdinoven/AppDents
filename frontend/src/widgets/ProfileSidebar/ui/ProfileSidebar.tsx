import s from "./ProfileSidebar.module.scss";
import { adminPanelTab, pagesTabs, subPagesTabs } from "../model/tabs.tsx";
import { SidebarShell } from "@/shared/components/ui/SidebarShell/SidebarShell.tsx";
import { useSelector } from "react-redux";
import { AppRootStateType } from "@/shared/store/store.ts";

export const ProfileSidebar = () => {
  const role = useSelector((state: AppRootStateType) => state.user.role);

  return (
    <div className={s.profile_sidebar}>
      <SidebarShell
        data={
          role === "admin" ? [adminPanelTab, ...subPagesTabs] : subPagesTabs
        }
      />
      <SidebarShell data={pagesTabs} />
    </div>
  );
};
