import { useParams } from "react-router-dom";
import DetailHeader from "../../modules/common/DetailHeader/DetailHeader.tsx";
import { adminApi } from "../../../../api/adminApi/adminApi.ts";
import { useEffect, useState } from "react";
import { getFormattedDate } from "../../../../common/helpers/helpers.ts";
import DateRangeFilter from "../../../../components/ui/DateRangeFilter/DateRangeFilter.tsx";
import Loader from "../../../../components/ui/Loader/Loader.tsx";
import SwitchButtons from "../../../../components/ui/SwitchButtons/SwitchButtons.tsx";
import s from "./LandingAnalytics.module.scss";
import LandingAnalyticsChart from "../../tabs/Analytics/Charts/LandingAnalyticsChart.tsx";

const LandingAnalytics = () => {
  const { landingId } = useParams();
  const [chartData, setChartData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [chartMode, setChartMode] = useState<"hour" | "day">("hour");
  const [dateRange, setDateRange] = useState(() => ({
    startDate: getFormattedDate(new Date()),
    endDate: getFormattedDate(new Date()),
  }));

  const handleStartDateChange = (value: string) => {
    setDateRange((prev) => ({ ...prev, startDate: value }));
  };

  const handleEndDateChange = (value: string) => {
    setDateRange((prev) => ({ ...prev, endDate: value }));
  };

  const fetchChartData = async () => {
    setLoading(true);

    const params = {
      landing_id: landingId,
      start_date: dateRange.startDate,
      end_date: dateRange.endDate,
      bucket: chartMode,
    };
    try {
      const res = await adminApi.getLandingTraffic(params);
      setChartData(res.data);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChartData();
  }, [dateRange, chartMode]);

  return (
    <div className={s.landing_analytics_container}>
      <DetailHeader
        link={"/admin?tab=analytics&content=listing"}
        title={"landing-traffic"}
      />
      <div className={s.filters}>
        <DateRangeFilter
          startDate={dateRange.startDate}
          endDate={dateRange.endDate}
          onEndDateChange={handleEndDateChange}
          onStartDateChange={handleStartDateChange}
        />
        <SwitchButtons
          buttonsArr={["hour", "day"]}
          activeValue={chartMode}
          handleClick={(val) => setChartMode(val)}
        />
      </div>
      {loading ? (
        <Loader />
      ) : (
        chartData && <LandingAnalyticsChart data={chartData} type={chartMode} />
      )}
    </div>
  );
};

export default LandingAnalytics;
