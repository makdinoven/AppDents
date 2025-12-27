import { Outlet } from "react-router-dom";
import s from "./AdminPage.module.scss";
import { Trans } from "react-i18next";
import { AdminSidebar, useAdminNav } from "@/widgets/admin/admin-sidebar";

const AdminPage = () => {
  const { currentTitleKey, sidebarMode } = useAdminNav();

  return (
    <div className={s.admin_page}>
      <AdminSidebar sidebarMode={sidebarMode} />
      <div className={s.admin_content}>
        {currentTitleKey && (
          <div className={s.admin_page_header}>
            <h2>
              <Trans i18nKey={currentTitleKey} />
            </h2>
          </div>
        )}

        <Outlet />
      </div>
    </div>
  );
};

export default AdminPage;
