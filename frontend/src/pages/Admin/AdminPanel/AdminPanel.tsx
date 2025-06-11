import s from "./AdminPanel.module.scss";
import { useSearchParams } from "react-router-dom";
import AdminCoursesTab from "../tabs/AdminCoursesTab.tsx";
import AdminLandingsTab from "../tabs/AdminLandingsTab.tsx";
import AdminAuthorsTab from "../tabs/AdminAuthorsTab.tsx";
import AdminUsersTab from "../tabs/AdminUsersTab.tsx";
import SelectableList from "../../../components/CommonComponents/SelectableList/SelectableList.tsx";
import Analytics from "../tabs/Analytics/Analytics.tsx";
import { useEffect } from "react";
import { FILTER_PARAM_KEYS } from "../../../common/helpers/commonConstants.ts";

const AdminPanel = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const tabFromParams = searchParams.get("tab");
  useEffect(() => {
    if (!tabFromParams) {
      const newParams = new URLSearchParams(searchParams);
      newParams.set("tab", "landings");
      setSearchParams(newParams);
    }
  }, [tabFromParams, searchParams, setSearchParams]);

  const activeTab = tabFromParams || "landings";

  const handleSelectTab = (value: string) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set("tab", value);
    newParams.delete(FILTER_PARAM_KEYS.language);
    newParams.delete(FILTER_PARAM_KEYS.size);
    if (value === "analytics") {
      newParams.delete("page");
    } else {
      newParams.delete("content");
      newParams.set("page", "1");
    }
    setSearchParams(newParams);
  };

  const tabs = [
    {
      name: "admin.landings.landings",
      value: "landings",
      component: <AdminLandingsTab />,
    },
    {
      name: "admin.courses.courses",
      value: "courses",
      component: <AdminCoursesTab />,
    },
    {
      name: "admin.authors.authors",
      value: "authors",
      component: <AdminAuthorsTab />,
    },
    { name: "admin.users.users", value: "users", component: <AdminUsersTab /> },
    {
      name: "admin.analytics.analytics",
      value: "analytics",
      component: <Analytics />,
    },
  ];

  return (
    <div className={s.admin}>
      <SelectableList
        items={tabs}
        activeValue={activeTab}
        onSelect={handleSelectTab}
      />

      {tabs.find((tab) => tab.value === activeTab)?.component}
    </div>
  );
};

export default AdminPanel;
