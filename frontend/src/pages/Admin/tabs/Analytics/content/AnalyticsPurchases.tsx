import { useEffect, useState } from "react";
import { getFormattedDate } from "../../../../../common/helpers/helpers.ts";
import s from "../Analytics.module.scss";
import DateRangeFilter from "../../../../../components/ui/DateRangeFilter/DateRangeFilter.tsx";
import { Trans } from "react-i18next";
import { adminApi } from "../../../../../api/adminApi/adminApi.ts";
import Loader from "../../../../../components/ui/Loader/Loader.tsx";
import Table from "../../../../../components/ui/Table/Table.tsx";

const AnalyticsPurchases = ({ title }: { title: string }) => {
  const [data, setData] = useState<any>(null);
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

  useEffect(() => {
    fetchData();
  }, [dateRange]);

  return (
    <>
      <h2>
        <Trans i18nKey={title} />
      </h2>
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
      )}
    </>
  );
};

export default AnalyticsPurchases;
