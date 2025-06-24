// import s from "../Analytics.module.scss"

import { useEffect, useState } from "react";
import { getFormattedDate } from "../../../../../common/helpers/helpers.tsx";
import { adminApi } from "../../../../../api/adminApi/adminApi.ts";
import s from "../Analytics.module.scss";
import DateRangeFilter from "../../../../../components/ui/DateRangeFilter/DateRangeFilter.tsx";
import UserGrowthChart from "../Charts/UserGrowthChart.tsx";
import Loader from "../../../../../components/ui/Loader/Loader.tsx";

const AnalyticsUserGrowth = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState(() => {
    const today = new Date();
    const oneWeekAgo = new Date();
    oneWeekAgo.setDate(today.getDate() - 7);

    return {
      startDate: getFormattedDate(oneWeekAgo),
      endDate: getFormattedDate(today),
    };
  });

  const handleStartDateChange = (value: string) => {
    setDateRange((prev) => ({ ...prev, startDate: value }));
  };

  const handleEndDateChange = (value: string) => {
    setDateRange((prev) => ({ ...prev, endDate: value }));
  };

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

      {!data && loading ? <Loader /> : <UserGrowthChart data={data.data} />}
    </>
  );
};

export default AnalyticsUserGrowth;
