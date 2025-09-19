import s from "./AdminPanel.module.scss";
import { useSearchParams } from "react-router-dom";
import SelectableList from "../../../components/CommonComponents/SelectableList/SelectableList.tsx";
import Analytics from "../tabs/Analytics/Analytics.tsx";
import { useEffect } from "react";
import { FILTER_PARAM_KEYS } from "../../../common/helpers/commonConstants.ts";
import AdminTools from "../tabs/AdminTools/AdminTools.tsx";
import AdminContent, {
  ADMIN_CONTENT_QUERY_KEY,
} from "../tabs/AdminContent/AdminContent.tsx";

const AdminPanel = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const tabFromParams = searchParams.get("tab");
  const defaultTabKey = "content";
  useEffect(() => {
    if (!tabFromParams) {
      const newParams = new URLSearchParams(searchParams);
      newParams.set("tab", defaultTabKey);
      setSearchParams(newParams);
    }
  }, [tabFromParams, searchParams, setSearchParams]);

  const activeTab = tabFromParams || defaultTabKey;

  const handleSelectTab = (value: string) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set("tab", value);
    newParams.delete(FILTER_PARAM_KEYS.language);
    newParams.delete(FILTER_PARAM_KEYS.size);
    if (value === "analytics" || value === "tools") {
      newParams.delete("page");
      newParams.delete(ADMIN_CONTENT_QUERY_KEY);
    } else {
      newParams.delete(ADMIN_CONTENT_QUERY_KEY);
      newParams.set("page", "1");
    }
    setSearchParams(newParams);
  };

  const tabs = [
    {
      name: "admin.content",
      value: "content",
      component: <AdminContent />,
    },
    {
      name: "admin.analytics.analytics",
      value: "analytics",
      component: <Analytics />,
    },
    {
      name: "admin.tools.tools",
      value: "tools",
      component: <AdminTools />,
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
