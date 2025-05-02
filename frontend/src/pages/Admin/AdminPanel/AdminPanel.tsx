import s from "./AdminPanel.module.scss";
import { useSearchParams } from "react-router-dom";
import { useEffect } from "react";
import Courses from "../tabs/Courses.tsx";
import Landings from "../tabs/Landings.tsx";
import Authors from "../tabs/Authors.tsx";
import Users from "../tabs/Users.tsx";
import SelectableList from "../../../components/CommonComponents/SelectableList/SelectableList.tsx";
import Analytics from "../tabs/Analytics/Analytics.tsx";

const AdminPanel = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get("tab") || "landings";

  const handleSelectTab = (value: string) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set("tab", value);
    newParams.set("page", "1");
    setSearchParams(newParams);
  };

  const tabs = [
    {
      name: "admin.landings.landings",
      value: "landings",
      component: <Landings />,
    },
    {
      name: "admin.courses.courses",
      value: "courses",
      component: <Courses />,
    },
    { name: "admin.authors.authors", value: "authors", component: <Authors /> },
    { name: "admin.users.users", value: "users", component: <Users /> },
    {
      name: "admin.analytics.analytics",
      value: "analytics",
      component: <Analytics />,
    },
  ];

  useEffect(() => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set("tab", activeTab);
    setSearchParams(newParams);
  }, [activeTab, searchParams, setSearchParams]);

  return (
    <div className={s.admin}>
      <SelectableList
        items={tabs}
        activeValue={activeTab}
        onSelect={handleSelectTab}
      />

      <div className={s.content}>
        {tabs.find((tab) => tab.value === activeTab)?.component}
      </div>
    </div>
  );
};

export default AdminPanel;
