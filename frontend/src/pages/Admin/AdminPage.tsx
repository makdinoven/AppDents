import { Outlet, useLocation } from "react-router-dom";
import AdminSidebar from "./AdminSidebar/AdminSidebar.tsx";
import s from "./AdminPage.module.scss";
import { Trans } from "react-i18next";
import { useState } from "react";
import { PATHS } from "../../app/routes/routes.ts";

const ADMIN_SIDEBAR_LINKS = [
  {
    label: "admin.content",
    innerLinks: [
      { label: "admin.landings.landings", link: PATHS.ADMIN_LANDINGS_LISTING },
      { label: "admin.courses.courses", link: PATHS.ADMIN_COURSES_LISTING },
      { label: "admin.authors.authors", link: PATHS.ADMIN_AUTHORS_LISTING },
      { label: "admin.users.users", link: PATHS.ADMIN_USERS_LISTING },
      { label: "admin.books.books", link: PATHS.ADMIN_BOOKS_LISTING },
      {
        label: "admin.bookLandings.bookLandings",
        link: PATHS.ADMIN_BOOK_LANDINGS_LISTING,
      },
    ],
  },
  {
    label: "admin.analytics.analytics",
    innerLinks: [
      {
        label: "admin.analytics.purchases",
        link: PATHS.ADMIN_ANALYTICS_PURCHASES,
      },
      {
        label: "admin.analytics.languageStats",
        link: PATHS.ADMIN_ANALYTICS_LANG_STATS,
      },
      {
        label: "admin.analytics.adListing",
        link: PATHS.ADMIN_ANALYTICS_AD_LISTING,
      },
      {
        label: "admin.analytics.referrals",
        link: PATHS.ADMIN_ANALYTICS_REFERRALS,
      },
      {
        label: "admin.analytics.userGrowth",
        link: PATHS.ADMIN_ANALYTICS_USER_GROWTH,
      },
      {
        label: "admin.analytics.freewebs",
        link: PATHS.ADMIN_ANALYTICS_FREEWEBS,
      },
      { label: "admin.analytics.traffic", link: PATHS.ADMIN_ANALYTICS_TRAFFIC },
      {
        label: "admin.analytics.searchQueries",
        link: PATHS.ADMIN_ANALYTICS_SEARCH_QUERIES,
      },
    ],
  },
  {
    label: "admin.adControl.adControl",
    innerLinks: [
      {
        label: "admin.adControl.listing",
        link: PATHS.ADMIN_AD_CONTOL_LISTING,
      },
      {
        label: "admin.adControl.accounts",
        link: PATHS.ADMIN_AD_CONTROL_ACCOUNTS,
      },
      {
        label: "admin.adControl.staff",
        link: PATHS.ADMIN_AD_CONTROL_STAFF,
      },
    ],
  },
  {
    label: "admin.tools.tools",
    innerLinks: [
      { label: "Video summary", link: PATHS.ADMIN_TOOLS_VIDEO_SUMMARY },
      { label: "Clip tool", link: PATHS.ADMIN_TOOLS_CLIP },
      { label: "Magic video fix", link: PATHS.ADMIN_TOOLS_MAGIC },
    ],
  },
];

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
        // <Sidebar
        //     sections={profileSidebarData}
        //     topSlot={<div>Admin panel</div>}
        //     renderItem={(item, close) => (
        //         <SidebarItem key={item.path} item={item} onClick={close} />
        //     )}
        // />
        <AdminSidebar
          links={ADMIN_SIDEBAR_LINKS}
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
