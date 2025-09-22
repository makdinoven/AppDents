import { useEffect, useState } from "react";
import { getFormattedDate } from "../../../../../common/helpers/helpers.ts";
import s from "../Analytics.module.scss";
import DateRangeFilter from "../../../../../components/ui/DateRangeFilter/DateRangeFilter.tsx";
import { adminApi } from "../../../../../api/adminApi/adminApi.ts";
import Loader from "../../../../../components/ui/Loader/Loader.tsx";
import Table from "../../../../../components/ui/Table/Table.tsx";
import PurchasesSourceChart from "../Charts/PurchasesSourceChart.tsx";
import MultiSelect from "../../../../../components/CommonComponents/MultiSelect/MultiSelect.tsx";
import { PAYMENT_SOURCES_OPTIONS } from "../../../../../common/helpers/commonConstants.ts";
import SwitchButtons from "../../../../../components/ui/SwitchButtons/SwitchButtons.tsx";

const AnalyticsPurchases = () => {
  const [data, setData] = useState<any>(null);
  const [chartData, setChartData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [chartMode, setChartMode] = useState<"count" | "amount">("count");
  const [chartSource, setChartSource] = useState<any>(null);
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

  const fetchData = async () => {
    setLoading(true);
    const params = {
      start_date: dateRange.startDate,
      end_date: dateRange.endDate,
    };
    try {
      const res = await adminApi.getPurchases(params);
      setData({
        items: res.data.items,
        total: res.data.total,
        total_amount: res.data.total_amount,
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
      ...(chartSource && chartSource !== "ALL" ? { source: chartSource } : {}),
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
  }, [dateRange]);

  useEffect(() => {
    fetchChartData();
  }, [dateRange, chartMode, chartSource]);

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
              Total:
              <span className={"highlight_blue_bold"}>{data.total}</span>
            </p>
            <p>
              Amount:
              <span className={"highlight_blue_bold"}>{data.total_amount}</span>
            </p>
          </>
        )}
      </div>

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
              selectedValue={chartSource}
              onChange={({ value }) => setChartSource(value as string)}
              valueKey={"value"}
              labelKey={"value"}
            />
            <SwitchButtons
              buttonsArr={["count", "amount"]}
              activeValue={chartMode}
              handleClick={(val) => setChartMode(val)}
            />
          </div>
          <PurchasesSourceChart data={chartData} type={chartMode} />
          <Table
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
