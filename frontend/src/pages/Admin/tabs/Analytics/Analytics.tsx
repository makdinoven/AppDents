import s from "./Analytics.module.scss";
import Tabs from "../../../../components/ui/Tabs/Tabs.tsx";
import AnalyticsLanguages from "./content/AnalyticsLanguages.tsx";
import AnalyticsListing from "./content/AnalyticsListing.tsx";
import AnalyticsReferrals from "./content/AnalyticsReferrals.tsx";
import { useSearchParams } from "react-router-dom";
import AnalyticsPurchases from "./content/AnalyticsPurchases.tsx";

const QUERY_KEY = "content";

const Analytics = () => {
  const [searchParams] = useSearchParams();
  const tabFromParams = searchParams.get(QUERY_KEY);

  const analyticsContent = [
    {
      name: "admin.analytics.landings",
      value: "landings",
      component: (title: string) => <AnalyticsLanguages title={title} />,
    },
    {
      name: "admin.analytics.listing",
      value: "listing",
      component: (title: string) => <AnalyticsListing title={title} />,
    },
    {
      name: "admin.analytics.referrals",
      value: "referrals",
      component: (title: string) => <AnalyticsReferrals title={title} />,
    },
    {
      name: "admin.analytics.purchases",
      value: "purchases",
      component: (title: string) => <AnalyticsPurchases title={title} />,
    },
  ];

  const activeTab = analyticsContent.find((tab) => tab.value === tabFromParams);

  return (
    <div className={s.analytics_page}>
      <Tabs queryKey={QUERY_KEY} mainTab={"landings"} tabs={analyticsContent} />

      {activeTab?.component(activeTab.name)}
    </div>
  );
};

export default Analytics;
