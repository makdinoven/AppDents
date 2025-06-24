import { useEffect, useState } from "react";
import { getFormattedDate } from "../../../../../common/helpers/helpers.tsx";
import { adminApi } from "../../../../../api/adminApi/adminApi.ts";
import s from "../Analytics.module.scss";
import DateRangeFilter from "../../../../../components/ui/DateRangeFilter/DateRangeFilter.tsx";
import Loader from "../../../../../components/ui/Loader/Loader.tsx";
import Table from "../../../../../components/ui/Table/Table.tsx";

const AnalyticsFreeCourses = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState(() => {
    const today = new Date();
    return {
      startDate: getFormattedDate(today),
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
      const res = await adminApi.getFreewebStats(params);
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
              Freeweb users:
              <span className={"highlight_blue_bold"}>
                {data.summary.freebie_users}
              </span>
            </p>
            <p>
              All freeweb users:
              <span className={"highlight_blue_bold"}>
                {data.summary.active_free_users}
              </span>
            </p>
          </>
        )}
      </div>

      {!data && loading ? (
        <Loader />
      ) : (
        <Table
          data={data.courses}
          columnLabels={{
            course_name: "Course",
            free_taken: "Count",
            converted_to_course: "Bought",
            converted_to_course_rate: "Buy rate",
            converted_to_any_course: "Bought another",
            converted_to_any_course_rate: "Bought another rate",
          }}
        />
      )}
    </>
  );
};

export default AnalyticsFreeCourses;
