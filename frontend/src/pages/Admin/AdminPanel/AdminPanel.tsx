import s from "./AdminPanel.module.scss";
import { useLocation, useNavigate } from "react-router-dom";
import FilterButton from "../../../components/ui/FilterButton/FilterButton.tsx";
import { useEffect, useState } from "react";
import Courses from "../tabs/Courses.tsx";
import Landings from "../tabs/Landings.tsx";
import Authors from "../tabs/Authors.tsx";
import Users from "../tabs/Users.tsx";

const AdminPanel = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const initialTab = queryParams.get("tab") || "landings";
  const [activeTab, setActiveTab] = useState(initialTab);

  const tabs = [
    {
      name: "landings",
      label: "admin.landings.landings",
      component: <Landings />,
    },
    {
      name: "courses",
      label: "admin.courses.courses",
      component: <Courses />,
    },
    { name: "authors", label: "admin.authors.authors", component: <Authors /> },
    { name: "users", label: "admin.users.users", component: <Users /> },
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
