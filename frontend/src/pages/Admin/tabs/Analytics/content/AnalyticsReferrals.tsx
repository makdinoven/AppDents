import { useEffect, useState } from "react";
import { adminApi } from "../../../../../api/adminApi/adminApi.ts";
import s from "../Analytics.module.scss";
import Table from "../../../../../components/ui/Table/Table.tsx";

const AnalyticsReferrals = () => {
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");
  // const [limit, setLimit] = useState<string>("10");
  const [data, setData] = useState<any>(null);

  const fetchReferrals = async () => {
    const params: {
      // limit: string;
      start_date?: string;
      end_date?: string;
    } = {
      // limit: limit,
    };

    if (startDate) {
      params.start_date = startDate;
    }
    if (endDate) {
      params.end_date = endDate;
    }

    try {
      const res = await adminApi.getReferrals(params);
      setData(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchReferrals();
  }, [endDate, startDate]);
  if (!data) return null;

  return (
    <>
      <div className={`${s.analytics_options} ${s.analytics_options_three}`}>
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
        {/*<MultiSelect*/}
        {/*  isSearchable={false}*/}
        {/*  id={"limits"}*/}
        {/*  options={ANALYTICS_LIMITS}*/}
        {/*  placeholder={""}*/}
        {/*  label={t("admin.analytics.size")}*/}
        {/*  selectedValue={limit}*/}
        {/*  isMultiple={false}*/}
        {/*  onChange={(e) => setLimit(e.value as string)}*/}
        {/*  valueKey="value"*/}
        {/*  labelKey="name"*/}
        {/*/>*/}
      </div>
      <Table
        title={"Inviters"}
        data={data.inviters}
        columnLabels={{
          inviter_id: "Inviter id",
          email: "Email",
          referrals: "Count",
          balance: "Balance",
          total_credited: "Total Credited",
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
  );
};

export default AnalyticsReferrals;
