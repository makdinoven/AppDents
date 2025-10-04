import s from "../Analytics.module.scss";
import MultiSelect from "../../../../../components/CommonComponents/MultiSelect/MultiSelect.tsx";
import {
  ANALYTICS_LIMITS,
  LANGUAGES_NAME,
} from "../../../../../common/helpers/commonConstants.ts";
import Table from "../../../../../components/ui/Table/Table.tsx";
import { useEffect, useState } from "react";
import { adminApi } from "../../../../../api/adminApi/adminApi.ts";
import DateRangeFilter from "../../../../../components/ui/DateRangeFilter/DateRangeFilter.tsx";
import Loader from "../../../../../components/ui/Loader/Loader.tsx";
import { Path } from "../../../../../routes/routes.ts";
import SortOrderToggle from "../../../../../components/ui/SortOrderToggle/SortOrderToggle.tsx";
import { useDateRangeFilter } from "../../../../../common/hooks/useDateRangeFilter.ts";
import Search from "../../../../../components/ui/Search/Search.tsx";
import { t } from "i18next";
import { useSearchParams } from "react-router-dom";

const AnalyticsListing = () => {
  const [searchParams] = useSearchParams();
  const [language, setLanguage] = useState<string>("EN");
  const [limit, setLimit] = useState<string>("500");
  const [landings, setLandings] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [totals, setTotals] = useState<any>(null);
  const [sortOrder, setSortOrder] = useState<"asc" | "desc" | null>(null);
  const [adSort, setAdSort] = useState<"ad" | "no-ad" | "all">("all");
  const {
    dateRange,
    handleStartDateChange,
    handleEndDateChange,
    selectedPreset,
    setPreset,
  } = useDateRangeFilter("custom");
  const analyticsSearch = "listing-search";
  const searchQuery = searchParams.get(analyticsSearch)?.toLowerCase() || "";

  useEffect(() => {
    fetchMostPopularLandings();
  }, [language, limit, dateRange, sortOrder]);

  const fetchMostPopularLandings = async () => {
    setLoading(true);
    const params: {
      language?: string;
      limit: string;
      start_date?: string;
      end_date?: string;
      sort_by?: string;
      sort_dir?: string;
    } = {
      limit: limit,
    };

    if (language !== "all") {
      params.language = language;
    }

    if (dateRange.startDate) {
      params.start_date = dateRange.startDate;
    }
    if (dateRange.endDate) {
      params.end_date = dateRange.endDate;
    }
    if (sortOrder) {
      params.sort_by = "created_at";
      params.sort_dir = sortOrder;
    }

    try {
      const res = await adminApi.getMostPopularLandings(params);
      setLandings(res.data.items);
      setTotals(res.data.totals);
      setLoading(false);
    } catch (err) {
      console.error(err);
    }
  };

  const filteredLandings = landings
    ?.filter((landing: any) => {
      if (adSort === "all") return true;
      if (adSort === "ad") return landing.in_advertising === true;
      if (adSort === "no-ad") return landing.in_advertising === false;
      return true;
    })
    ?.filter((landing: any) => {
      if (!searchQuery) return true;
      return (
        landing.landing_name?.toLowerCase().includes(searchQuery) ||
        String(landing.id).includes(searchQuery)
      );
    });

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

        <div className={s.column_two_items}>
          <MultiSelect
            isSearchable={false}
            id={"language"}
            options={LANGUAGES_NAME}
            placeholder={"Choose a language"}
            selectedValue={language}
            isMultiple={false}
            onChange={(e) => setLanguage(e.value as string)}
            valueKey="value"
            labelKey="name"
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
        </div>

        <div className={s.column_two_items}>
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
          <SortOrderToggle
            transKey={"Date"}
            sortOrder={sortOrder}
            setSortOrder={setSortOrder}
          />
        </div>
      </div>
      {totals && (
        <div className={s.totals}>
          <p>
            Total sales(Ad): <span>{totals.ad_sales_total}</span>
          </p>
          <p>
            Total sales: <span>{totals.sales_total}</span>
          </p>
        </div>
      )}

      {!landings && loading ? (
        <Loader />
      ) : (
        <>
          <Search
            id={analyticsSearch}
            placeholder={t("admin.landings.search")}
          />
          <Table
            loading={loading}
            data={filteredLandings}
            landingLinkByIdPath={Path.landingAnalytics}
            columnLabels={{
              id: "ID",
              landing_name: "Name",
              sales_count: "Sales",
              language: "Lang",
              in_advertising: "Ad",
              ad_sales_count: "Sales(Ad)",
              created_at: "Created",
            }}
          />
        </>
      )}
    </>
  );
};

export default AnalyticsListing;
