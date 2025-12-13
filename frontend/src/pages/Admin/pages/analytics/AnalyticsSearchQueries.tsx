import { useEffect, useState } from "react";
import { adminApi } from "../../../../shared/api/adminApi/adminApi.ts";
import s from "./Analytics.module.scss";
import DateRangeFilter from "../../../../shared/components/ui/DateRangeFilter/DateRangeFilter.tsx";
import Loader from "../../../../shared/components/ui/Loader/Loader.tsx";
import Table from "../../../../shared/components/ui/Table/Table.tsx";
import { useDateRangeFilter } from "../../../../shared/common/hooks/useDateRangeFilter.ts";
import Search from "../../../../shared/components/ui/Search/Search.tsx";
import { t } from "i18next";
import { useSearchParams } from "react-router-dom";

const AnalyticsSearchQueries = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [searchParams, setSearchParams] = useSearchParams();
  const {
    dateRange,
    handleStartDateChange,
    handleEndDateChange,
    selectedPreset,
    setPreset,
  } = useDateRangeFilter("today");
  const queriesSearch = "queries-search";
  const searchQuery = searchParams.get(queriesSearch)?.toLowerCase() || "";

  const fetchData = async () => {
    setLoading(true);
    const params = {
      start_date: dateRange.startDate,
      end_date: dateRange.endDate,
    };

    try {
      const res = await adminApi.getSearchQueries(params);
      setData(res.data);
      console.log(res.data);
      setLoading(false);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchData();
  }, [dateRange]);

  const handleSearch = (val: string) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set(queriesSearch, val);
    setSearchParams(newParams);
  };

  const filteredQueries = data?.items.filter((item: any) => {
    if (!searchQuery) return true;
    return item.query?.toLowerCase().includes(searchQuery);
  });

  return (
    <>
      <div className={s.analytics_options}>
        <DateRangeFilter
          startDate={dateRange.startDate}
          endDate={dateRange.endDate}
          selectedPreset={selectedPreset}
          setPreset={setPreset}
          onEndDateChange={handleEndDateChange}
          onStartDateChange={handleStartDateChange}
        />
      </div>

      {data && (
        <div className={s.totals}>
          <p>
            All search queries:
            <span className={"highlight_blue_bold"}>{data.count}</span>
          </p>
        </div>
      )}

      {!data && loading ? (
        <Loader />
      ) : (
        <>
          <Search
            valueFromUrl={searchQuery}
            onChangeValue={handleSearch}
            id={queriesSearch}
            placeholder={t("admin.analytics.searchQueries")}
          />
          <Table
            loading={loading}
            data={filteredQueries}
            columnLabels={{
              query: "Query",
              count: "Count",
              unique_users: "Unique users",
            }}
          />
        </>
      )}
    </>
  );
};

export default AnalyticsSearchQueries;
