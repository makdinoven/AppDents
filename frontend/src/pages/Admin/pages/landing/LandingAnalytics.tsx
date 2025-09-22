import s from "./LandingAnalytics.module.scss";
import { useParams } from "react-router-dom";
import DetailHeader from "../../modules/common/DetailHeader/DetailHeader.tsx";
import { adminApi } from "../../../../api/adminApi/adminApi.ts";
import { useEffect, useState } from "react";
import { getFormattedDate } from "../../../../common/helpers/helpers.ts";
import DateRangeFilter from "../../../../components/ui/DateRangeFilter/DateRangeFilter.tsx";
import Loader from "../../../../components/ui/Loader/Loader.tsx";

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
      setChartData(res.data.data);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChartData();
  }, [dateRange, chartMode]);

  useEffect(() => {
    console.log(chartData);
  }, [chartData]);

  return (
    <div>
      <DetailHeader
        link={"/admin?tab=analytics&content=listing"}
        title={"landing-traffic"}
      />
      {loading ? (
        <Loader />
      ) : (
        <>
          <DateRangeFilter
            startDate={dateRange.startDate}
            endDate={dateRange.endDate}
            onEndDateChange={handleEndDateChange}
            onStartDateChange={handleStartDateChange}
          />
          <div className={s.toggle_btns_container}>
            {["hour", "day"].map((mode) => (
              <button
                key={mode}
                className={`${chartMode === mode ? s.active : ""}`}
                onClick={() => setChartMode(mode as "hour" | "day")}
              >
                {mode}
              </button>
            ))}
          </div>
          {/*<PurchasesSourceChart data={chartData} type={chartMode} />*/}
        </>
      )}
    </div>
  );
};

export default LandingAnalytics;
