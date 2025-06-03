import s from "../Analytics.module.scss";
import Table from "../../../../../components/ui/Table/Table.tsx";
import { useEffect, useState } from "react";
import { adminApi } from "../../../../../api/adminApi/adminApi.ts";

const getFormattedDate = (date: Date) => {
  return date.toISOString().split("T")[0];
};

const AnalyticsLanguages = () => {
  const [languageStats, setLanguageStats] = useState<[] | null>(null);
  const [startDate, setStartDate] = useState<string>(() =>
    getFormattedDate(new Date()),
  );
  const [endDate, setEndDate] = useState<string>(() =>
    getFormattedDate(new Date()),
  );

  const handleStartDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setStartDate(e.target.value);
  };

  const handleEndDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEndDate(e.target.value);
  };

  useEffect(() => {
    fetchLandingsStats();
  }, [startDate, endDate]);

  const fetchLandingsStats = async () => {
    const params = {
      start_date: startDate,
      end_date: endDate,
    };

    try {
      const res = await adminApi.getLanguageStats(params);
      setLanguageStats(res.data.data);
    } catch (err) {
      console.error(err);
    }
  };

  if (!languageStats) return;

  return (
    <>
      <div className={s.totals_row}>
        <p>
          Total sales:
          <span className={"highlight_blue_bold"}>
            {languageStats.reduce((sum, item: any) => sum + item.count, 0)}
          </span>
        </p>
        <p>
          Total amount:
          <span className={"highlight_blue_bold"}>
            {languageStats
              .reduce(
                (sum, item: any) => sum + parseFloat(item.total_amount),
                0,
              )
              .toFixed(2)}{" "}
            $
          </span>
        </p>
      </div>
      <div className={s.analytics_options}>
        <div className={s.input_wrapper}>
          <label htmlFor="start_date">Start date</label>
          <input
            id="start_date"
            value={startDate}
            className={s.date_input}
            onChange={handleStartDateChange}
            type="date"
          />
        </div>
        <div className={s.input_wrapper}>
          <label htmlFor="end_date">End date</label>
          <input
            id="end_date"
            value={endDate}
            className={s.date_input}
            onChange={handleEndDateChange}
            type="date"
          />
        </div>
      </div>
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
    </>
  );
};

export default AnalyticsLanguages;
