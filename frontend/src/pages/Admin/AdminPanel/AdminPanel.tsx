import s from "./AdminPanel.module.scss";
import { useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import Courses from "../tabs/Courses.tsx";
import Landings from "../tabs/Landings.tsx";
import Authors from "../tabs/Authors.tsx";
import Users from "../tabs/Users.tsx";
import SelectableList from "../../../components/CommonComponents/SelectableList/SelectableList.tsx";

const AdminPanel = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const initialTab = queryParams.get("tab") || "landings";
  const [activeTab, setActiveTab] = useState(initialTab);

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
  ];

  useEffect(() => {
    navigate(`?tab=${activeTab}`, { replace: true });
  }, [activeTab, navigate]);

  return (
    <div className={s.admin}>
      <SelectableList
        items={tabs}
        activeValue={activeTab}
        onSelect={setActiveTab}
      />
      <div className={s.content}>
        {tabs.find((tab) => tab.value === activeTab)?.component}
      </div>
    </div>
  );
};

export default AdminPanel;
