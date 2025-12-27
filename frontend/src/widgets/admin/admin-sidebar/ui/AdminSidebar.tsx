import { Sidebar, SidebarItem } from "@/shared/ui/sidebar";
import { ADMIN_SIDEBAR_SECTIONS } from "../model/config.tsx";
import { useLocation } from "react-router-dom";

export const AdminSidebar = ({
  sidebarMode,
}: {
  sidebarMode: "full" | "collapsed";
}) => {
  const { pathname } = useLocation();

  return (
    <Sidebar
      persistKey={"admin-sidebar.collapsed"}
      autoCollapse={sidebarMode === "collapsed"}
      autoCollapseKey={pathname}
      sections={ADMIN_SIDEBAR_SECTIONS}
      renderItem={(item, close) => (
        <SidebarItem
          key={item.path}
          item={item}
          onClick={close}
          isCollapsed={false}
        />
      )}
    />
  );
};
