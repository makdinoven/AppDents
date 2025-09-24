// import s from "../Analytics.module.scss"

import { useEffect, useState } from "react";
import { adminApi } from "../../../../../api/adminApi/adminApi.ts";
import s from "../Analytics.module.scss";
import DateRangeFilter from "../../../../../components/ui/DateRangeFilter/DateRangeFilter.tsx";
import UserGrowthChart from "../Charts/UserGrowthChart.tsx";
import Loader from "../../../../../components/ui/Loader/Loader.tsx";
import { useDateRangeFilter } from "../../../../../common/hooks/useDateRangeFilter.ts";

const AnalyticsUserGrowth = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const {
    dateRange,
    handleStartDateChange,
    handleEndDateChange,
    selectedPreset,
    setPreset,
  } = useDateRangeFilter("lastWeek");

  const fetchData = async () => {
    setLoading(true);
    const params = {
      start_date: dateRange.startDate,
      end_date: dateRange.endDate,
    };

    try {
      const res = await adminApi.getUserGrowth(params);
      setData(res.data);
      setLoading(false);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchData();
  }, [dateRange]);

  return (
    <>
      <div className={s.analytics_options}>
        <DateRangeFilter
          startDate={dateRange.startDate}
          endDate={dateRange.endDate}
          onEndDateChange={handleEndDateChange}
          onStartDateChange={handleStartDateChange}
          selectedPreset={selectedPreset}
          setPreset={setPreset}
        />
        {data && (
          <>
            <p>
              Registered:
              <span className={"highlight_blue_bold"}>
                {data.total_new_users}
              </span>
            </p>
            <p>
              Total Users:
              <span className={"highlight_blue_bold"}>
                {data.end_total_users}
              </span>
            </p>
          </>
        )}
      </div>

      {!data && loading ? (
        <Loader />
      ) : (
        <UserGrowthChart loading={loading} data={data.data} />
      )}
    </>
  );
};

export default AnalyticsUserGrowth;
