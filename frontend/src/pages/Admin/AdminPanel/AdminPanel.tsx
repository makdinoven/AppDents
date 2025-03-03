import s from "./AdminPanel.module.scss";
import { useLocation, useNavigate } from "react-router-dom";
import Courses from "../tabs/Courses.tsx";
import FilterButton from "../../../components/ui/FilterButton/FilterButton.tsx";
import { useEffect, useState } from "react";
import Users from "../tabs/Users.tsx";
import { t } from "i18next";
import Authors from "../tabs/Authors.tsx";
import Landings from "../tabs/Landings.tsx";

const AdminPanel = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const initialTab = queryParams.get("tab") || "courses";
  const [activeTab, setActiveTab] = useState(initialTab);

  const tabs = [
    {
      name: "landings",
      label: t("admin.landings"),
      component: <Landings />,
    },
    {
      name: "courses",
      label: t("admin.courses"),
      component: <Courses />,
    },
    { name: "users", label: t("admin.users"), component: <Users /> },
    { name: "authors", label: t("admin.authors"), component: <Authors /> },
  ];

  useEffect(() => {
    navigate(`?tab=${activeTab}`, { replace: true });
  }, [activeTab, navigate]);

  return (
    <div className={s.admin}>
      <div className={s.tabs}>
        {tabs.map((tab) => (
          <FilterButton
            key={tab.name}
            text={tab.label}
            isActive={activeTab === tab.name}
            onClick={() => setActiveTab(tab.name)}
          />
        ))}
      </div>
      <div className={s.content}>
        {tabs.find((tab) => tab.name === activeTab)?.component}
      </div>
    </div>
  );
};

export default AdminPanel;
