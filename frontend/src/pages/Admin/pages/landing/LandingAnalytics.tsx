import { useParams } from "react-router-dom";
import DetailHeader from "../../modules/common/DetailHeader/DetailHeader.tsx";
import { adminApi } from "../../../../api/adminApi/adminApi.ts";
import { useEffect, useState } from "react";
import {
  formatIsoToLocalDatetime,
  getFormattedDate,
} from "../../../../common/helpers/helpers.ts";
import DateRangeFilter from "../../../../components/ui/DateRangeFilter/DateRangeFilter.tsx";
import Loader from "../../../../components/ui/Loader/Loader.tsx";
import SwitchButtons from "../../../../components/ui/SwitchButtons/SwitchButtons.tsx";
import s from "./LandingAnalytics.module.scss";
import LandingAnalyticsChart from "../../tabs/Analytics/Charts/LandingAnalyticsChart.tsx";
import Table from "../../../../components/ui/Table/Table.tsx";

const LandingAnalytics = () => {
  const { landingId } = useParams();
  const [chartData, setChartData] = useState<any>(null);
  const [chartMode, setChartMode] = useState<"hour" | "day">("day");
  const [landing, setLanding] = useState<{
    data: any;
    totals: { all: any; range: any };
    periods: { start: string; end: string }[];
  } | null>(null);
  const [dateRange, setDateRange] = useState({
    startDate: "",
    endDate: "",
  });

  const handleStartDateChange = (value: string) => {
    setDateRange((prev) => ({ ...prev, startDate: value }));
  };

  const handleEndDateChange = (value: string) => {
    setDateRange((prev) => ({ ...prev, endDate: value }));
  };

  const fetchChartData = async () => {
    const params: {
      landing_id: string;
      bucket: string;
      start_date?: string;
      end_date?: string;
    } = {
      landing_id: landingId!,
      bucket: chartMode,
    };
    if (dateRange.startDate) {
      params.start_date = dateRange.startDate;
    }
    if (dateRange.endDate) {
      params.end_date = dateRange.endDate;
    }
    try {
      const res = await adminApi.getLandingTraffic(params);
      setChartData(res.data.series);
      setLanding({
        data: res.data.landing,
        totals: { all: res.data.totals_all_time, range: res.data.totals_range },
        periods: res.data.ad_periods,
      });
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchChartData();
  }, [dateRange, chartMode]);

  useEffect(() => {
    if (landing?.data?.created_at) {
      const createdAt = getFormattedDate(new Date(landing.data.created_at));
      const today = getFormattedDate(new Date());

      setDateRange({
        startDate: createdAt,
        endDate: today,
      });
    }
  }, [landing?.data?.created_at]);

  return (
    <div className={s.landing_analytics_container}>
      <DetailHeader
        link={"/admin?tab=analytics&content=listing"}
        title={landing?.data.name}
      />
      {landing ? (
        <>
          <span className={s.created_at}>
            Created: {formatIsoToLocalDatetime(landing.data.created_at, true)}
          </span>
          <div className={s.filters}>
            <DateRangeFilter
              startDate={dateRange.startDate}
              endDate={dateRange.endDate}
              onEndDateChange={handleEndDateChange}
              onStartDateChange={handleStartDateChange}
            />
            <SwitchButtons
              buttonsArr={["hour", "day"]}
              activeValue={chartMode}
              handleClick={(val) => setChartMode(val)}
            />
          </div>
          <div className={s.info_container}>
            <Table
              title="Range data"
              data={[
                { metric: "Purchases", value: landing.totals.range.purchases },
                { metric: "Visits", value: landing.totals.range.visits },
                {
                  metric: "Visits from ad",
                  value: landing.totals.range.ad_visits,
                },
              ]}
              columnLabels={{ metric: "Metric", value: "Value" }}
            />

            <Table
              title="All time data"
              data={[
                {
                  metric: "Conversion",
                  value: `${landing.totals.all.conversion_percent.toFixed(2)}%`,
                },
                {
                  metric: "Purchases from first visit",
                  value: landing.totals.all.purchases_first_visit,
                },
                {
                  metric: "All time purchases",
                  value: landing.totals.all.purchases,
                },
                {
                  metric: "All time visits",
                  value: landing.totals.all.visits,
                },
                {
                  metric: "Visits from ad",
                  value: landing.totals.all.ad_visits,
                },
              ]}
              columnLabels={{ metric: "Metric", value: "Value" }}
            />
          </div>

          {chartData && (
            <LandingAnalyticsChart data={chartData} type={chartMode} />
          )}

          <Table
            title="Start/End Ad"
            data={landing.periods}
            columnLabels={{ start: "Start date", end: "End date" }}
          />
        </>
      ) : (
        <Loader />
      )}
    </div>
  );
};

export default LandingAnalytics;
