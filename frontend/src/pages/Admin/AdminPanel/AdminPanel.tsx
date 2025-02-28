import s from "./AdminPanel.module.scss";
import { useLocation, useNavigate } from "react-router-dom";
import Courses from "./modules/Courses.tsx";
import TabButton from "../../../components/ui/TabButton/TabButton.tsx";
import { useEffect, useState } from "react";
import Users from "./modules/Users.tsx";
import { t } from "i18next";
import Authors from "./modules/Authors.tsx";

const AdminPanel = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const initialTab = queryParams.get("tab") || "courses";
  const [activeTab, setActiveTab] = useState(initialTab);

  const tabs = [
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
          <TabButton
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
