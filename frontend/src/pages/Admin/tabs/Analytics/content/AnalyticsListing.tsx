import s from "../Analytics.module.scss";
import MultiSelect from "../../../../../components/CommonComponents/MultiSelect/MultiSelect.tsx";
import {
  ANALYTICS_LIMITS,
  LANGUAGES,
} from "../../../../../common/helpers/commonConstants.ts";
import { t } from "i18next";
import Table from "../../../../../components/ui/Table/Table.tsx";
import { useEffect, useState } from "react";
import { adminApi } from "../../../../../api/adminApi/adminApi.ts";

const AnalyticsListing = () => {
  const [language, setLanguage] = useState<string>("EN");
  const [limit, setLimit] = useState<string>("10");
  const [landings, setLandings] = useState<[] | null>(null);

  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");

  useEffect(() => {
    fetchMostPopularLandings();
  }, [language, limit, endDate, startDate]);

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

    if (startDate) {
      params.start_date = startDate;
    }
    if (endDate) {
      params.end_date = endDate;
    }

    try {
      const res = await adminApi.getMostPopularLandings(params);
      setLandings(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  if (!landings) return;

  return (
    <>
      <div className={s.analytics_options}>
        <div className={s.input_wrapper}>
          <label htmlFor="start_date">Start date</label>
          <input
            id="start_date"
            placeholder="Start date"
            value={startDate}
            className={s.date_input}
            onChange={(e) => setStartDate(e.target.value)}
            type="date"
          />
        </div>
        <div className={s.input_wrapper}>
          <label htmlFor="end_date">End date</label>
          <input
            id="end_date"
            placeholder="End date"
            value={endDate}
            className={s.date_input}
            onChange={(e) => setEndDate(e.target.value)}
            type="date"
          />
        </div>
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
          options={ANALYTICS_LIMITS}
          placeholder={""}
          label={t("admin.analytics.size")}
          selectedValue={limit}
          isMultiple={false}
          onChange={(e) => setLimit(e.value as string)}
          valueKey="value"
          labelKey="name"
        />
      </div>
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
    </>
  );
};

export default AnalyticsListing;
