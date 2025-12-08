import { useEffect, useState } from "react";
import s from "./Analytics.module.scss";
import DateRangeFilter from "../../../../shared/components/ui/DateRangeFilter/DateRangeFilter.tsx";
import { adminApi } from "../../../../shared/api/adminApi/adminApi.ts";
import Loader from "../../../../shared/components/ui/Loader/Loader.tsx";
import Table from "../../../../shared/components/ui/Table/Table.tsx";
import PurchasesSourceChart from "./Charts/PurchasesSourceChart.tsx";
import MultiSelect from "../../../../shared/components/ui/MultiSelect/MultiSelect.tsx";
import { PAYMENT_SOURCES_OPTIONS } from "../../../../shared/common/helpers/commonConstants.ts";
import SwitchButtons from "../../../../shared/components/ui/SwitchButtons/SwitchButtons.tsx";
import { useDateRangeFilter } from "../../../../shared/common/hooks/useDateRangeFilter.ts";

const AnalyticsPurchases = () => {
  const [data, setData] = useState<any>(null);
  const [chartData, setChartData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [chartMode, setChartMode] = useState<"count" | "amount">("count");
  const [source, setSource] = useState<any>(null);
  const {
    dateRange,
    handleStartDateChange,
    handleEndDateChange,
    selectedPreset,
    setPreset,
  } = useDateRangeFilter("today");

  const fetchData = async () => {
    setLoading(true);
    const params: { start_date?: string; end_date?: string } = {
      start_date: dateRange.startDate,
      end_date: dateRange.endDate,
      ...(source && source !== "ALL" ? { source: source } : {}),
    };
    try {
      const res = await adminApi.getPurchases(params);
      setData({
        items: res.data.items,
        total: res.data.total,
        total_amount: res.data.total_amount,
        total_amount_from_ad: res.data.total_amount_from_ad,
      });
      setLoading(false);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchChartData = async () => {
    const params = {
      start_date: dateRange.startDate,
      end_date: dateRange.endDate,
      mode: chartMode,
      ...(source && source !== "ALL" ? { source: source } : {}),
    };
    try {
      const res = await adminApi.getPurchasesSourceChart(params);
      setChartData(res.data.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchData();
  }, [dateRange, source]);

  useEffect(() => {
    fetchChartData();
  }, [dateRange, chartMode, source]);

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
      </div>

      {data && (
        <div className={s.totals}>
          <p>
            Total:
            <span className={"highlight_blue_bold"}>{data.total}</span>
          </p>
          <p>
            Amount:
            <span className={"highlight_blue_bold"}>{data.total_amount}</span>
          </p>
          <p>
            From ad:
            <span className={"highlight_blue_bold"}>
              {data.total_amount_from_ad}
            </span>
          </p>
        </div>
      )}

      {!data && loading ? (
        <Loader />
      ) : (
        <>
          <div className={s.two_items}>
            <MultiSelect
              id={"src_select"}
              options={PAYMENT_SOURCES_OPTIONS}
              placeholder={"Select source"}
              isMultiple={false}
              selectedValue={source}
              onChange={({ value }) => setSource(value as string)}
              valueKey={"value"}
              labelKey={"value"}
            />
            <SwitchButtons
              buttonsArr={["count", "amount"]}
              activeValue={chartMode}
              handleClick={(val) => setChartMode(val)}
            />
          </div>
          {chartData && (
            <PurchasesSourceChart
              loading={loading}
              data={chartData}
              type={chartMode}
            />
          )}

          <Table
            loading={loading}
            data={data.items}
            columnLabels={{
              email: "Email",
              amount: "Amount",
              source: "Source",
              from_ad: "Ad",
              paid_at: "Payment date",
            }}
          />
        </>
      )}
    </>
  );
};

export default AnalyticsPurchases;
