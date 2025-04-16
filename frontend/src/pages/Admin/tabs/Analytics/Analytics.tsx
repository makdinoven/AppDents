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

  useEffect(() => {
    fetchLandingsStats();
  }, []);

  useEffect(() => {
    fetchMostPopularLandings();
  }, [language, limit]);

  const fetchMostPopularLandings = async () => {
    try {
      const res = await adminApi.getMostPopularLandings({
        language: language,
        limit: limit,
      });
      setLandings(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchLandingsStats = async () => {
    try {
      const res = await adminApi.getLanguageStats();
      setLanguageStats(res.data.data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className={s.analytics_page}>
      <div className={s.top}>
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
        {languageStats && (
          <div className={s.languages_table}>
            <Table
              data={languageStats}
              columnLabels={{ language: "Lang", count: "Sales" }}
            />
          </div>
        )}
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
