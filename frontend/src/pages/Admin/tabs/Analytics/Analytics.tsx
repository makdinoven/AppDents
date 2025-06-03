import s from "./Analytics.module.scss";
import Tabs from "../../../../components/ui/Tabs/Tabs.tsx";
import AnalyticsLanguages from "./content/AnalyticsLanguages.tsx";
import AnalyticsListing from "./content/AnalyticsListing.tsx";
import AnalyticsReferrals from "./content/AnalyticsReferrals.tsx";
import { useSearchParams } from "react-router-dom";

const QUERY_KEY = "content";

const Analytics = () => {
  const [searchParams] = useSearchParams();
  const tabFromParams = searchParams.get(QUERY_KEY);

  const analyticsContent = [
    {
      name: "admin.analytics.landings",
      value: "landings",
      component: <AnalyticsLanguages />,
    },
    {
      name: "admin.analytics.listing",
      value: "listing",
      component: <AnalyticsListing />,
    },
    {
      name: "admin.analytics.referrals",
      value: "referrals",
      component: <AnalyticsReferrals />,
    },
  ];

  return (
    <div className={s.analytics_page}>
      <Tabs queryKey={QUERY_KEY} mainTab={"landings"} tabs={analyticsContent} />

      {analyticsContent.find((tab) => tab.value === tabFromParams)?.component}
    </div>
  );
};

export default Analytics;
