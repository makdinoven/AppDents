import s from "../Analytics.module.scss";
import Table from "../../../../../components/ui/Table/Table.tsx";
import { useEffect, useState } from "react";
import { adminApi } from "../../../../../api/adminApi/adminApi.ts";
import DateRangeFilter from "../../../../../components/ui/DateRangeFilter/DateRangeFilter.tsx";
import { getFormattedDate } from "../../../../../common/helpers/helpers.tsx";
import Loader from "../../../../../components/ui/Loader/Loader.tsx";

const AnalyticsLanguages = () => {
  const [languageStats, setLanguageStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
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

  useEffect(() => {
    fetchLandingsStats();
  }, [dateRange]);

  const fetchLandingsStats = async () => {
    setLoading(true);
    const params = {
      start_date: dateRange.startDate,
      end_date: dateRange.endDate,
    };

    try {
      const res = await adminApi.getLanguageStats(params);
      setLanguageStats(res.data.data);
      setLoading(false);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <>
      <div className={s.analytics_options}>
        <DateRangeFilter
          startDate={dateRange.startDate}
          endDate={dateRange.endDate}
          onEndDateChange={handleEndDateChange}
          onStartDateChange={handleStartDateChange}
        />
        {languageStats && (
          <>
            <p>
              Sales:
              <span className={"highlight_blue_bold"}>
                {languageStats.reduce(
                  (sum: number, item: any) => sum + item.count,
                  0,
                )}
              </span>
            </p>
            <p>
              Amount:
              <span className={"highlight_blue_bold"}>
                {languageStats
                  .reduce(
                    (sum: number, item: any) =>
                      sum + parseFloat(item.total_amount),
                    0,
                  )
                  .toFixed(2)}{" "}
                $
              </span>
            </p>
          </>
        )}
      </div>
      {!languageStats && loading ? (
        <Loader />
      ) : (
        <div className={s.languages_table}>
          <Table
            data={languageStats}
            columnLabels={{
              language: "Lang",
              count: "Sales",
              total_amount: "Total",
            }}
          />
        </div>
      )}
    </>
  );
};

export default AnalyticsLanguages;
