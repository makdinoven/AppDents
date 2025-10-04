import s from "./AdControlTab.module.scss";
import Tabs from "../../../../components/ui/Tabs/Tabs.tsx";
import { useSearchParams } from "react-router-dom";
import AdControlMain from "./content/AdControlMain/AdControlMain.tsx";
import AdControlAccounts from "./content/AdControlAccounts.tsx";
import AdControlStaff from "./content/AdControlStaff.tsx";

const QUERY_KEY = "ad-content";

const AdControlTab = () => {
  const [searchParams] = useSearchParams();
  const tabFromParams = searchParams.get(QUERY_KEY);

  const content = [
    {
      name: "Main",
      value: "main",
      component: <AdControlMain />,
    },
    {
      name: "Ad accounts",
      value: "accounts",
      component: <AdControlAccounts />,
    },
    {
      name: "Staff",
      value: "Staff",
      component: <AdControlStaff />,
    },
  ];

  const activeTab = content.find((tab) => tab.value === tabFromParams);

  return (
    <div className={s.ad_control_tab}>
      <Tabs queryKey={QUERY_KEY} mainTab={"main"} tabs={content} />
      {activeTab?.component}
    </div>
  );
};

export default AdControlTab;
