import s from "../Analytics/Analytics.module.scss";
import Tabs from "../../../../components/ui/Tabs/Tabs.tsx";
import { useSearchParams } from "react-router-dom";
import AdminLandingsList from "./content/AdminLandingsList.tsx";
import AdminCoursesList from "./content/AdminCoursesList.tsx";
import AdminBookLandingsList from "./content/AdminBookLandingsList.tsx";
import AdminBooksList from "./content/AdminBooksList.tsx";
import AdminAuthorsList from "./content/AdminAuthorsList.tsx";
import AdminUsersList from "./content/AdminUsersList.tsx";

export const ADMIN_CONTENT_QUERY_KEY = "content";

const Analytics = () => {
  const [searchParams] = useSearchParams();
  const tabFromParams = searchParams.get(ADMIN_CONTENT_QUERY_KEY);

  const content = [
    {
      name: "admin.landings.landings",
      value: "landings",
      component: <AdminLandingsList />,
    },
    {
      name: "admin.courses.courses",
      value: "courses",
      component: <AdminCoursesList />,
    },
    {
      name: "admin.book-landings.bookLandings",
      value: "book-landings",
      component: <AdminBookLandingsList />,
    },
    {
      name: "admin.books.books",
      value: "books",
      component: <AdminBooksList />,
    },
    {
      name: "admin.authors.authors",
      value: "authors",
      component: <AdminAuthorsList />,
    },
    {
      name: "admin.users.users",
      value: "users",
      component: <AdminUsersList />,
    },
  ];

  const activeTab = content.find((tab) => tab.value === tabFromParams);

  return (
    <div className={s.analytics_page}>
      <Tabs
        queryKey={ADMIN_CONTENT_QUERY_KEY}
        mainTab={"landings"}
        tabs={content}
      />
      {activeTab?.component}
    </div>
  );
};

export default Analytics;
