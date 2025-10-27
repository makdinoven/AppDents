import { Outlet, useLocation } from "react-router-dom";
import AdminSidebar from "./AdminSidebar/AdminSidebar.tsx";
import s from "./AdminPage.module.scss";
import { ADMIN_SIDEBAR_LINKS } from "../../common/helpers/commonConstants.ts";
import { Trans } from "react-i18next";
import { useState } from "react";

const AdminPage = () => {
  const [isSidebarMinimized, setIsSidebarMinimized] = useState(false);
  const location = useLocation();
  const showSidebar =
    !location.pathname.includes("/detail/") &&
    !location.pathname.includes("/landing-analytics/") &&
    !location.pathname.includes("/book-landing-analytics/");
  const currentPage =
    ADMIN_SIDEBAR_LINKS.flatMap((s) => s.innerLinks ?? []).find((l) =>
      location.pathname.startsWith(l.link),
    )?.label ?? null;

  return (
    <div
      className={`${showSidebar ? s.admin_page : ""} ${isSidebarMinimized ? s.minimized_sidebar : ""}`}
    >
      {showSidebar && (
        <AdminSidebar
          isMinimized={isSidebarMinimized}
          setIsMinimized={setIsSidebarMinimized}
        />
      )}
      <div className={s.admin_content}>
        {currentPage && (
          <div className={s.admin_page_header}>
            <h2>
              <Trans i18nKey={currentPage} />
            </h2>
          </div>
        )}

        <Outlet />
      </div>
    </div>
  );
};

export default AdminPage;
