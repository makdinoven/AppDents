import { useEffect, useState } from "react";
import { adminApi } from "../../../../shared/api/adminApi/adminApi.ts";
import { useDateRangeFilter } from "../../../../shared/common/hooks/useDateRangeFilter.ts";
import s from "./Analytics.module.scss";
import DateRangeFilter from "../../../../shared/components/ui/DateRangeFilter/DateRangeFilter.tsx";
import SwitchButtons from "../../../../shared/components/ui/SwitchButtons/SwitchButtons.tsx";
import LandingAnalyticsChart from "./Charts/LandingAnalyticsChart.tsx";
import Loader from "../../../../shared/components/ui/Loader/Loader.tsx";
import MultiSelect from "../../../../shared/components/MultiSelect/MultiSelect.tsx";
import { LANGUAGES_NAME } from "../../../../shared/common/helpers/commonConstants.ts";
import Table from "../../../../shared/components/ui/Table/Table.tsx";

const AnalyticsTraffic = () => {
  const [loading, setLoading] = useState(false);
  const [chartData, setChartData] = useState<any>(null);
  const [chartMode, setChartMode] = useState<"hour" | "day">("day");
  const [totals, setTotals] = useState<{ all: any; range: any }>({
    all: null,
    range: null,
  });
  const [language, setLanguage] = useState<string>("EN");
  const {
    dateRange,
    handleStartDateChange,
    handleEndDateChange,
    selectedPreset,
    setPreset,
  } = useDateRangeFilter("today");

  const fetchData = async () => {
    setLoading(true);

    const params: {
      bucket: string;
      start_date?: string;
      end_date?: string;
      language?: string;
    } = {
      bucket: chartMode,
    };

    if (language !== "all") {
      params.language = language;
    }
    if (dateRange.startDate) {
      params.start_date = dateRange.startDate;
    }
    if (dateRange.endDate) {
      params.end_date = dateRange.endDate;
    }
    try {
      const res = await adminApi.getSiteTraffic(params);
      setChartData(res.data.series);
      setTotals({
        all: res.data.totals_all_time,
        range: res.data.totals_range,
      });
      setLoading(false);
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [dateRange, chartMode]);

  return !chartData && loading ? (
    <Loader />
  ) : (
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
        <MultiSelect
          isSearchable={false}
          id={"language"}
          options={LANGUAGES_NAME}
          placeholder={"Choose a language"}
          selectedValue={language}
          isMultiple={false}
          onChange={(e) => setLanguage(e.value as string)}
          valueKey="value"
          labelKey="name"
        />
        <SwitchButtons
          buttonsArr={["hour", "day"]}
          activeValue={chartMode}
          handleClick={(val) => setChartMode(val)}
        />
      </div>

      {chartData && (
        <LandingAnalyticsChart
          loading={loading}
          data={chartData}
          type={chartMode}
        />
      )}

      {totals.range && (
        <Table
          loading={loading}
          title="Range data"
          data={[
            { metric: "Visits", value: totals.range.visits },
            { metric: "Purchases", value: totals.range.purchases },
            { metric: "Ad purchases", value: totals.range.ad_purchases },
            {
              metric: "Visits from ad",
              value: totals.range.ad_visits,
            },
          ]}
          columnLabels={{ metric: "Metric", value: "Value" }}
        />
      )}

      {totals.all && (
        <Table
          loading={loading}
          title="All time data"
          data={[
            {
              metric: "All time purchases",
              value: totals.all.purchases,
            },
            {
              metric: "All time visits",
              value: totals.all.visits,
            },
            {
              metric: "Visits from ad",
              value: totals.all.ad_visits,
            },
            {
              metric: "Ad purchases",
              value: totals.all.ad_purchases,
            },
          ]}
          columnLabels={{ metric: "Metric", value: "Value" }}
        />
      )}
    </>
  );
};

export default AnalyticsTraffic;
