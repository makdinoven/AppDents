import s from "./Analytics.module.scss";
import Tabs from "../../../../components/ui/Tabs/Tabs.tsx";
import AnalyticsLanguages from "./content/AnalyticsLanguages.tsx";
import AnalyticsListing from "./content/AnalyticsListing.tsx";
import AnalyticsReferrals from "./content/AnalyticsReferrals.tsx";
import { useSearchParams } from "react-router-dom";
import AnalyticsPurchases from "./content/AnalyticsPurchases.tsx";
import AnalyticsUserGrowth from "./content/AnalyticsUserGrowth.tsx";
import AnalyticsFreeCourses from "./content/AnalyticsFreeCourses.tsx";
import AnalyticsTraffic from "./content/AnalyticsTraffic.tsx";

const QUERY_KEY = "content";

const Analytics = () => {
  const [searchParams] = useSearchParams();
  const tabFromParams = searchParams.get(QUERY_KEY);

  const analyticsContent = [
    {
      name: "admin.analytics.purchases",
      value: "purchases",
      component: <AnalyticsPurchases />,
    },
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
    {
      name: "admin.analytics.userGrowth",
      value: "user_growth",
      component: <AnalyticsUserGrowth />,
    },
    {
      name: "admin.analytics.freeCourses",
      value: "free_courses",
      component: <AnalyticsFreeCourses />,
    },
    {
      name: "admin.analytics.traffic",
      value: "traffic",
      component: <AnalyticsTraffic />,
    },
    // {
    //   name: "admin.analytics.videoCheck",
    //   value: "video_check",
    //   component: <AnalyticsVideoCheck />,
    // },
  ];

  const activeTab = analyticsContent.find((tab) => tab.value === tabFromParams);

  return (
    <div className={s.analytics_page}>
      <Tabs
        queryKey={QUERY_KEY}
        mainTab={"purchases"}
        tabs={analyticsContent}
      />
      {/*<h2>*/}
      {/*  <Trans i18nKey={activeTab?.name} />*/}
      {/*</h2>*/}
      {activeTab?.component}
    </div>
  );
};

export default Analytics;
