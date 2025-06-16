import { useEffect, useState } from "react";
import { adminApi } from "../../../../../api/adminApi/adminApi.ts";
import s from "../Analytics.module.scss";
import Table from "../../../../../components/ui/Table/Table.tsx";
import DateRangeFilter from "../../../../../components/ui/DateRangeFilter/DateRangeFilter.tsx";
import Loader from "../../../../../components/ui/Loader/Loader.tsx";

const AnalyticsReferrals = () => {
  // const [limit, setLimit] = useState<string>("10");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState(() => ({
    startDate: "",
    endDate: "",
  }));

  const handleStartDateChange = (value: string) => {
    setDateRange((prev) => ({ ...prev, startDate: value }));
  };

  const handleEndDateChange = (value: string) => {
    setDateRange((prev) => ({ ...prev, endDate: value }));
  };

  const fetchReferrals = async () => {
    const params: {
      // limit: string;
      start_date?: string;
      end_date?: string;
    } = {
      // limit: limit,
    };

    if (dateRange.startDate) {
      params.start_date = dateRange.startDate;
    }
    if (dateRange.endDate) {
      params.end_date = dateRange.endDate;
    }

    try {
      const res = await adminApi.getReferrals(params);
      setData(res.data);
      setLoading(false);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchReferrals();
  }, [dateRange]);

  return (
    <>
      <div className={s.analytics_options}>
        <DateRangeFilter
          startDate={dateRange.startDate}
          endDate={dateRange.endDate}
          onEndDateChange={handleEndDateChange}
          onStartDateChange={handleStartDateChange}
        />
      </div>
      {loading ? (
        <Loader />
      ) : (
        <>
          <Table
            title={"Inviters"}
            data={data.inviters}
            columnLabels={{
              inviter_id: "Inviter id",
              email: "Email",
              referrals: "Count",
              balance: "Balance",
              total_credited: "Spend",
            }}
          />
          <Table
            title={"Referral users"}
            data={data.referrals}
            columnLabels={{
              inviter_email: "Inviter email",
              referral_email: "Referral email",
              registered_at: "Register date",
            }}
          />
        </>
      )}
    </>
  );
};

export default AnalyticsReferrals;
