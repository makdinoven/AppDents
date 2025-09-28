import s from "../Analytics.module.scss";
import Table from "../../../../../components/ui/Table/Table.tsx";
import { useEffect, useState } from "react";
import { adminApi } from "../../../../../api/adminApi/adminApi.ts";
import DateRangeFilter from "../../../../../components/ui/DateRangeFilter/DateRangeFilter.tsx";
import Loader from "../../../../../components/ui/Loader/Loader.tsx";
import LangPurchasesChart from "../Charts/LangPurchasesChart.tsx";
import { useDateRangeFilter } from "../../../../../common/hooks/useDateRangeFilter.ts";
import SwitchButtons from "../../../../../components/ui/SwitchButtons/SwitchButtons.tsx";
import AdminField from "../../../modules/common/AdminField/AdminField.tsx";

const AnalyticsLanguages = () => {
  const [languageStats, setLanguageStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCurrency, setSelectedCurrency] = useState<"eur" | "usd">(
    "usd",
  );
  const [exchangeRate, setExchangeRate] = useState("0.85");
  const {
    dateRange,
    handleStartDateChange,
    handleEndDateChange,
    selectedPreset,
    setPreset,
  } = useDateRangeFilter("today");

  useEffect(() => {
    fetchLandingsStats();
  }, [dateRange]);

  const convertAmount = (amount: string, currency: "usd" | "eur") => {
    const num = parseFloat(amount.replace("$", ""));
    if (currency === "eur") {
      return `${(num * parseFloat(exchangeRate)).toFixed(2)} €`;
    }
    return `${num.toFixed(2)} $`;
  };

  const convertedTotals = languageStats?.total.map((item: any) => ({
    ...item,
    total_amount: convertAmount(item.total_amount, selectedCurrency),
  }));

  const convertedDaily = languageStats?.daily.map((day: any) => ({
    ...day,
    languages: day.languages.map((lang: any) => ({
      ...lang,
      total_amount: convertAmount(lang.total_amount, selectedCurrency),
    })),
  }));

  const fetchLandingsStats = async () => {
    setLoading(true);
    const params = {
      start_date: dateRange.startDate,
      end_date: dateRange.endDate,
    };

    try {
      const res = await adminApi.getLanguageStats(params);
      setLanguageStats(res.data);
      setLoading(false);
    } catch (err) {
      console.error(err);
    }
  };

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
        {languageStats && (
          <>
            <p>
              Sales:
              <span className={"highlight_blue_bold"}>
                {languageStats.total.reduce(
                  (sum: number, item: any) => sum + item.count,
                  0,
                )}
              </span>
            </p>
            <div className={s.currency_total_container}>
              <div className={s.currency_items}>
                <AdminField
                  className={s.currency_input}
                  id={"exchange_rate"}
                  type={"input"}
                  inputType={"number"}
                  value={exchangeRate}
                  onChange={(e: any) => setExchangeRate(e.value)}
                />
                <SwitchButtons
                  buttonsArr={["eur", "usd"]}
                  activeValue={selectedCurrency}
                  handleClick={(val) => setSelectedCurrency(val)}
                />
              </div>

              <p>
                Amount:
                <span className={"highlight_blue_bold"}>
                  {(
                    languageStats.total.reduce(
                      (sum: number, item: any) =>
                        sum + parseFloat(item.total_amount),
                      0,
                    ) *
                    (selectedCurrency === "eur" ? parseFloat(exchangeRate) : 1)
                  ).toFixed(2)}{" "}
                  {selectedCurrency.toUpperCase()}
                </span>
              </p>
            </div>
          </>
        )}
      </div>
      {!languageStats && loading ? (
        <Loader />
      ) : (
        <div className={s.languages_content}>
          <div className={s.languages_table}>
            <Table
              loading={loading}
              data={convertedTotals}
              columnLabels={{
                language: "Lang",
                count: "Sales",
                total_amount: "Total",
              }}
            />
          </div>
          <LangPurchasesChart loading={loading} data={convertedDaily} />
        </div>
      )}
    </>
  );
};

export default AnalyticsLanguages;
