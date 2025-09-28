import { useEffect, useState } from "react";
import { adminApi } from "../../../../../api/adminApi/adminApi.ts";
import s from "../Analytics.module.scss";
import Table from "../../../../../components/ui/Table/Table.tsx";
import DateRangeFilter from "../../../../../components/ui/DateRangeFilter/DateRangeFilter.tsx";
import Loader from "../../../../../components/ui/Loader/Loader.tsx";
import { useDateRangeFilter } from "../../../../../common/hooks/useDateRangeFilter.ts";

const AnalyticsReferrals = () => {
  // const [limit, setLimit] = useState<string>("10");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const {
    dateRange,
    handleStartDateChange,
    handleEndDateChange,
    selectedPreset,
    setPreset,
  } = useDateRangeFilter("custom");

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

    setLoading(true);

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
          selectedPreset={selectedPreset}
          setPreset={setPreset}
        />
      </div>
      {!data && loading ? (
        <Loader />
      ) : (
        <>
          <Table
            title={"Inviters"}
            data={data.inviters}
            loading={loading}
            columnLabels={{
              inviter_id: "Inviter id",
              email: "Email",
              referrals: "Count",
              balance: "Balance",
              total_credited: "Spend",
            }}
          />
          <Table
            loading={loading}
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
