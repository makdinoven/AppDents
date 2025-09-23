import s from "../Analytics.module.scss";
import MultiSelect from "../../../../../components/CommonComponents/MultiSelect/MultiSelect.tsx";
import {
  ANALYTICS_LIMITS,
  LANGUAGES,
} from "../../../../../common/helpers/commonConstants.ts";
import Table from "../../../../../components/ui/Table/Table.tsx";
import { useEffect, useState } from "react";
import { adminApi } from "../../../../../api/adminApi/adminApi.ts";
import DateRangeFilter from "../../../../../components/ui/DateRangeFilter/DateRangeFilter.tsx";
import Loader from "../../../../../components/ui/Loader/Loader.tsx";
import { Path } from "../../../../../routes/routes.ts";
import SortByDate from "../../../../../components/ui/SortOrderToggle/SortOrderToggle.tsx";

const AnalyticsListing = () => {
  const [language, setLanguage] = useState<string>("EN");
  const [limit, setLimit] = useState<string>("500");
  const [landings, setLandings] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc" | null>(
    null,
  );
  const [adSort, setAdSort] = useState<"ad" | "no-ad" | "all">("all");

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

  const handleSortDirectionChange = (direction: "asc" | "desc") => {
    if (direction === sortDirection) {
      setSortDirection(null);
    } else {
      setSortDirection(direction);
    }
  };

  useEffect(() => {
    fetchMostPopularLandings();
  }, [language, limit, dateRange, sortDirection]);

  const fetchMostPopularLandings = async () => {
    setLoading(true);
    const params: {
      language: string;
      limit: string;
      start_date?: string;
      end_date?: string;
      sort_by?: string;
      sort_dir?: string;
    } = {
      language: language,
      limit: limit,
    };

    if (dateRange.startDate) {
      params.start_date = dateRange.startDate;
    }
    if (dateRange.endDate) {
      params.end_date = dateRange.endDate;
    }
    if (sortDirection) {
      params.sort_by = "created_at";
      params.sort_dir = sortDirection;
    }

    try {
      const res = await adminApi.getMostPopularLandings(params);
      setLandings(res.data);
      setLoading(false);
    } catch (err) {
      console.error(err);
    }
  };

  const filteredLandings = landings?.filter((landing: any) => {
    if (adSort === "all") return true;
    if (adSort === "ad") return landing.in_advertising === true;
    if (adSort === "no-ad") return landing.in_advertising === false;
    return true;
  });

  return (
    <>
      <div className={s.analytics_options}>
        <DateRangeFilter
          startDate={dateRange.startDate}
          endDate={dateRange.endDate}
          onEndDateChange={handleEndDateChange}
          onStartDateChange={handleStartDateChange}
        />
        <MultiSelect
          isSearchable={false}
          id={"language"}
          options={LANGUAGES}
          placeholder={"Choose a language"}
          selectedValue={language}
          isMultiple={false}
          onChange={(e) => setLanguage(e.value as string)}
          valueKey="value"
          labelKey="label"
        />
        <MultiSelect
          isSearchable={false}
          id={"limits"}
          options={ANALYTICS_LIMITS}
          placeholder={""}
          selectedValue={limit}
          isMultiple={false}
          onChange={(e) => setLimit(e.value as string)}
          valueKey="value"
          labelKey="name"
        />
        <SortByDate
          transKey={"Date"}
          activeBtn={sortDirection}
          handleBtnClick={handleSortDirectionChange}
        />
        <MultiSelect
          isSearchable={false}
          id={"sort_add"}
          options={[
            { value: "all", name: "All ads" },
            { value: "ad", name: "Ad" },
            { value: "no-ad", name: "No ad" },
          ]}
          placeholder={""}
          selectedValue={adSort}
          isMultiple={false}
          onChange={(e) => setAdSort(e.value as "all" | "no-ad" | "ad")}
          valueKey="value"
          labelKey="name"
        />
      </div>
      {!landings && loading ? (
        <Loader />
      ) : (
        <Table
          data={filteredLandings}
          landingLinkByIdPath={Path.landingAnalytics}
          columnLabels={{
            id: "ID",
            landing_name: "Name",
            sales_count: "Sales",
            language: "Lang",
            in_advertising: "Ad",
          }}
        />
      )}
    </>
  );
};

export default AnalyticsListing;
