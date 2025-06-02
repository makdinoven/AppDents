import s from "./Analytics.module.scss";
import MultiSelect from "../../../../components/CommonComponents/MultiSelect/MultiSelect.tsx";
import { LANGUAGES } from "../../../../common/helpers/commonConstants.ts";
import { t } from "i18next";
import { useEffect, useState } from "react";
import { adminApi } from "../../../../api/adminApi/adminApi.ts";
import Table from "../../../../components/ui/Table/Table.tsx";

const LIMITS = [
  { name: "10", value: "10" },
  { name: "20", value: "20" },
  { name: "50", value: "50" },
  { name: "100", value: "100" },
  { name: "200", value: "200" },
  { name: "500", value: "500" },
];

const Analytics = () => {
  const [language, setLanguage] = useState<string>("EN");
  const [limit, setLimit] = useState<string>("10");
  const [landings, setLandings] = useState<[] | null>(null);
  const [languageStats, setLanguageStats] = useState<[] | null>(null);
  const getFormattedDate = (date: Date) => {
    return date.toISOString().split("T")[0];
  };
  const [startDate, setStartDate] = useState<string>(() =>
    getFormattedDate(new Date()),
  );
  const [endDate, setEndDate] = useState<string>(() =>
    getFormattedDate(new Date()),
  );

  const [secondStartDate, setSecondStartDate] = useState<string>("");
  const [secondEndDate, setSecondEndDate] = useState<string>("");

  useEffect(() => {
    fetchLandingsStats();
  }, [startDate, endDate]);

  useEffect(() => {
    fetchMostPopularLandings();
  }, [language, limit, secondEndDate, secondStartDate]);

  const fetchMostPopularLandings = async () => {
    const params: {
      language: string;
      limit: string;
      start_date?: string;
      end_date?: string;
    } = {
      language: language,
      limit: limit,
    };

    if (secondStartDate) {
      params.start_date = secondStartDate;
    }
    if (secondEndDate) {
      params.end_date = secondEndDate;
    }

    try {
      const res = await adminApi.getMostPopularLandings(params);
      setLandings(res.data);
    } catch (err) {
      console.error(err);
    }
  };

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

  const handleStartDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setStartDate(e.target.value);
  };

  const handleEndDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEndDate(e.target.value);
  };

  return (
    <div className={s.analytics_page}>
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
      {languageStats && (
        <>
          <div className={s.totals_row}>
            <div>
              Total sales:
              <span className={"highlight_blue_bold"}>
                {languageStats.reduce((sum, item: any) => sum + item.count, 0)}
              </span>
            </div>
            <span>
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
            </span>
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
      )}

      <div className={s.analytics_options}>
        <MultiSelect
          isSearchable={false}
          id={"language"}
          options={LANGUAGES}
          placeholder={"Choose a language"}
          label={t("admin.landings.language")}
          selectedValue={language}
          isMultiple={false}
          onChange={(e) => setLanguage(e.value as string)}
          valueKey="value"
          labelKey="label"
        />
        <MultiSelect
          isSearchable={false}
          id={"limits"}
          options={LIMITS}
          placeholder={""}
          label={t("admin.analytics.size")}
          selectedValue={limit}
          isMultiple={false}
          onChange={(e) => setLimit(e.value as string)}
          valueKey="value"
          labelKey="name"
        />
      </div>
      <div className={s.analytics_options}>
        <div className={s.input_wrapper}>
          <label htmlFor="start_date">Start date</label>
          <input
            id="start_date"
            value={secondStartDate}
            className={s.date_input}
            onChange={(e) => setSecondStartDate(e.target.value)}
            type="date"
          />
        </div>
        <div className={s.input_wrapper}>
          <label htmlFor="end_date">End date</label>
          <input
            id="end_date"
            value={secondEndDate}
            className={s.date_input}
            onChange={(e) => setSecondEndDate(e.target.value)}
            type="date"
          />
        </div>
      </div>
      {landings && (
        <Table
          data={landings}
          columnLabels={{
            id: "ID",
            landing_name: "Name",
            sales_count: "Sales",
            language: "Lang",
            in_advertising: "Ad",
          }}
        />
      )}
    </div>
  );
};

export default Analytics;
