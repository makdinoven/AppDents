import { useSelector } from "react-redux";
import { AppRootStateType } from "@/shared/store/store";
import { Sidebar } from "@/shared/ui/sidebar";
import { UserProfileInfo } from "@/features/user-profile-info";
import { LogOutBtn } from "@/features/log-out";
import { adminPanelTab, pagesTabs, subPagesTabs } from "../../model/tabs";
import { SidebarItem } from "@/shared/ui/sidebar/SidebarItem/SidebarItem";

export const ProfileSidebar = () => {
  const role = useSelector((state: AppRootStateType) => state.user.role);
  const subPages =
    role === "admin" ? [adminPanelTab, ...subPagesTabs] : subPagesTabs;
  const sections = [subPages, pagesTabs];

  return (
    <Sidebar
      sections={sections}
      topSlot={<UserProfileInfo />}
      bottomSlot={<LogOutBtn />}
      renderItem={(item, close) => (
        <SidebarItem key={item.path} item={item} onClick={close} />
      )}
    />
  );
};
