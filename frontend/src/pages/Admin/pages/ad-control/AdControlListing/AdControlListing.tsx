import s from "./AdControlListing.module.scss";
import DateRangeFilter from "../../../../../components/ui/DateRangeFilter/DateRangeFilter.tsx";
import MultiSelect from "../../../../../components/CommonComponents/MultiSelect/MultiSelect.tsx";
import { LANGUAGES_NAME } from "../../../../../common/helpers/commonConstants.ts";
import SortOrderToggle, {
  SortDirectionType,
} from "../../../../../components/ui/SortOrderToggle/SortOrderToggle.tsx";
import MinMaxFilter from "../../../../../components/ui/MinMaxFilter/MinMaxFilter.tsx";
import Search from "../../../../../components/ui/Search/Search.tsx";
import { t } from "i18next";
import Table from "../../../../../components/ui/Table/Table.tsx";
import { Path } from "../../../../../routes/routes.ts";
import Loader from "../../../../../components/ui/Loader/Loader.tsx";
import { useSearchParams } from "react-router-dom";
import { useEffect, useState } from "react";
import useDebounce from "../../../../../common/hooks/useDebounce.ts";
import { useDateRangeFilter } from "../../../../../common/hooks/useDateRangeFilter.ts";
import { adminApi } from "../../../../../api/adminApi/adminApi.ts";
import { Alert } from "../../../../../components/ui/Alert/Alert.tsx";
import { ErrorIcon } from "../../../../../assets/icons";
import { transformIdNameArrToValueNameArr } from "../../../../../common/helpers/helpers.ts";
import SwitchButtons from "../../../../../components/ui/SwitchButtons/SwitchButtons.tsx";

const adControlSearch = "ad-control-q";

type ColorType = "green" | "orange" | "red" | "white" | "black";

const AdControlListing = () => {
  const [mode, setMode] = useState<"courses" | "books">("courses");
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState<boolean>(false);
  const [language, setLanguage] = useState<string>("all");
  const [data, setData] = useState<any>(null);
  const searchQuery = searchParams.get(adControlSearch)?.toLowerCase() || "";
  const debauncedSearchQuery = useDebounce(searchQuery, 300);
  const [sortOrder, setSortOrder] = useState<"asc" | "desc" | null>(null);
  const [colors, setColors] = useState<ColorType[]>([]);
  const [cycleRange, setCycleRange] = useState<{
    min: string;
    max: string;
  } | null>(null);
  const [daysRange, setDaysRange] = useState<{
    min: string;
    max: string;
  } | null>(null);
  const [purchases10Range, setPurchases10Range] = useState<{
    min: string;
    max: string;
  } | null>(null);
  const [adVisitsRange, setAdVisitsRange] = useState<{
    min: string;
    max: string;
  } | null>(null);
  const [totalPurchasesRange, setTotalPurchasesRange] = useState<{
    min: string;
    max: string;
  } | null>(null);
  const [totalAdPurchasesRange, setTotalAdPurchasesRange] = useState<{
    min: string;
    max: string;
  } | null>(null);
  const [sortBy, setSortBy] = useState("");
  const [staffList, setStaffList] = useState<any>([]);
  const [accountsList, setAccountsList] = useState<any>([]);
  const [selectedStaff, setSelectedStaff] = useState<number | "all">("all");
  const [selectedAccount, setSelectedAccount] = useState<number | "all">("all");
  const {
    dateRange,
    handleStartDateChange,
    handleEndDateChange,
    selectedPreset,
    setPreset,
  } = useDateRangeFilter("custom");

  const fetchData = async () => {
    setLoading(true);
    const params: {
      q?: string;
      stage_start_from?: string;
      stage_start_to?: string;
      language?: string;
      sort_dir?: SortDirectionType;
      colors?: ColorType[];
      cycle_min?: number;
      cycle_max?: number;
      first5_min?: number;
      first5_max?: number;
      sales10_min?: number;
      sales10_max?: number;
      av10d_min?: number;
      av10d_max?: number;
      tp10d_min?: number;
      tp10d_max?: number;
      apall_min?: number;
      apall_max?: number;
      days_min?: number;
      days_max?: number;
      sort_by?: string;
      staff_id?: number;
      account_id?: number;
    } = {};

    if (language !== "all") {
      params.language = language;
    }
    if (dateRange.startDate) {
      params.stage_start_from = dateRange.startDate;
    }
    if (dateRange.endDate) {
      params.stage_start_to = dateRange.endDate;
    }

    if (sortOrder) {
      params.sort_dir = sortOrder;
    }
    if (colors && !!colors.length) {
      params.colors = colors;
    }
    if (debauncedSearchQuery) {
      params.q = debauncedSearchQuery;
    }
    if (daysRange) {
      if (daysRange.min) {
        params.days_min = Number(daysRange.min);
      }
      if (daysRange.max) {
        params.days_max = Number(daysRange.max);
      }
    }
    if (cycleRange) {
      if (cycleRange.min) {
        params.cycle_min = Number(cycleRange.min);
      }
      if (cycleRange.max) {
        params.cycle_max = Number(cycleRange.max);
      }
    }
    if (purchases10Range) {
      if (purchases10Range.min) {
        params.sales10_min = Number(purchases10Range.min);
      }
      if (purchases10Range.max) {
        params.sales10_max = Number(purchases10Range.max);
      }
    }

    if (adVisitsRange) {
      if (adVisitsRange.min) {
        params.av10d_min = Number(adVisitsRange.min);
      }
      if (adVisitsRange.max) {
        params.av10d_max = Number(adVisitsRange.max);
      }
    }

    if (totalPurchasesRange) {
      if (totalPurchasesRange.min) {
        params.tp10d_min = Number(totalPurchasesRange.min);
      }
      if (totalPurchasesRange.max) {
        params.tp10d_max = Number(totalPurchasesRange.max);
      }
    }

    if (totalAdPurchasesRange) {
      if (totalAdPurchasesRange.min) {
        params.apall_min = Number(totalAdPurchasesRange.min);
      }
      if (totalAdPurchasesRange.max) {
        params.apall_max = Number(totalAdPurchasesRange.max);
      }
    }

    if (sortBy && sortBy !== "all") {
      params.sort_by = sortBy;
    }
    if (selectedStaff && selectedStaff !== "all") {
      params.staff_id = selectedStaff;
    }
    if (selectedAccount && selectedAccount !== "all") {
      params.account_id = selectedAccount;
    }
    try {
      let res;
      if (mode === "courses") {
        res = await adminApi.getAdControlOverview(params);
      } else {
        res = await adminApi.getAdControlOverviewBooks(params);
      }

      setData(res.data.items);

      setLoading(false);
    } catch {
      Alert("Error fetching data", <ErrorIcon />);
      setLoading(false);
    }
  };

  const fetchStaff = async () => {
    try {
      const res = await adminApi.getAdStaffList();
      setStaffList(transformIdNameArrToValueNameArr(res.data, true));
    } catch (error) {
      console.error(error);
    }
  };

  const fetchAccounts = async () => {
    try {
      const res = await adminApi.getAdAccountsList();
      setAccountsList(transformIdNameArrToValueNameArr(res.data, true));
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    fetchData();
  }, [
    debauncedSearchQuery,
    dateRange,
    language,
    sortOrder,
    colors,
    cycleRange?.min,
    cycleRange?.max,
    daysRange?.min,
    daysRange?.max,
    purchases10Range?.min,
    purchases10Range?.max,
    adVisitsRange?.min,
    adVisitsRange?.max,
    totalPurchasesRange?.min,
    totalPurchasesRange?.max,
    totalAdPurchasesRange?.min,
    totalAdPurchasesRange?.max,
    sortBy,
    selectedStaff,
    selectedAccount,
    mode,
  ]);

  useEffect(() => {
    fetchAccounts();
    fetchStaff();
  }, []);

  const handleClearFilters = () => {
    const confirmed = window.confirm("Are you sure?");
    if (!confirmed) return;

    setPreset("custom");
    setSortOrder(null);
    setColors([]);
    setCycleRange(null);
    setPurchases10Range(null);
    setDaysRange(null);
    setSortBy("");
    setLanguage("EN");
    setSelectedAccount("all");
    setSelectedStaff("all");
  };

  return !data && loading ? (
    <Loader />
  ) : (
    <div className={s.ad_control_main}>
      <SwitchButtons
        useTranslation={false}
        buttonsArr={["courses", "books"]}
        activeValue={mode}
        handleClick={(mode) => setMode(mode)}
      />
      <div className={s.filters}>
        <div className={s.filters_row}>
          <DateRangeFilter
            startDate={dateRange.startDate}
            endDate={dateRange.endDate}
            onEndDateChange={handleEndDateChange}
            onStartDateChange={handleStartDateChange}
            selectedPreset={selectedPreset}
            setPreset={setPreset}
          />
          <div className={s.sort_filters}>
            <MultiSelect
              isSearchable={false}
              id={"sort_by"}
              label={"Sort by"}
              options={[
                { name: "All", value: "all" },
                { name: "Purchases (last 10d)", value: "sales10" },
                { name: "Days in", value: "days" },
                { name: "Cycle", value: "cycle" },
                { name: "Landing name", value: "name" },
                { name: "Language", value: "language" },
                { name: "Stage start", value: "stage_start" },
                { name: "Color", value: "color" },
              ]}
              placeholder={"Select sort"}
              selectedValue={sortBy}
              isMultiple={false}
              onChange={(val) => setSortBy(val.value as string)}
              valueKey="value"
              labelKey="name"
            />
            <SortOrderToggle
              sortOrder={sortOrder}
              setSortOrder={setSortOrder}
            />
          </div>
        </div>

        <div className={s.filters_row}>
          {staffList && (
            <MultiSelect
              isSearchable={false}
              label={"Staff"}
              id={"staff"}
              options={staffList}
              placeholder={"Choose staff members"}
              selectedValue={selectedStaff !== "all" ? selectedStaff : ""}
              isMultiple={false}
              onChange={(val) => setSelectedStaff(Number(val.value))}
              valueKey="value"
              labelKey="name"
            />
          )}
          {accountsList && (
            <MultiSelect
              isSearchable={false}
              id={"accounts"}
              label={"Ad accounts"}
              options={accountsList}
              placeholder={"Choose ad accounts"}
              selectedValue={selectedAccount !== "all" ? selectedAccount : ""}
              isMultiple={false}
              onChange={(val) => setSelectedAccount(Number(val.value))}
              valueKey="value"
              labelKey="name"
            />
          )}
        </div>

        <div className={s.filters_row}>
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
            id={"color"}
            options={[
              { name: "White", value: "white" },
              { name: "Red", value: "red" },
              { name: "Orange", value: "orange" },
              { name: "Green", value: "green" },
              { name: "Black", value: "black" },
            ]}
            placeholder={"Choose a color"}
            selectedValue={colors}
            isMultiple={true}
            onChange={(val) => setColors(val.value as ColorType[])}
            valueKey="value"
            labelKey="name"
          />
        </div>

        <div className={s.filters_row}>
          <MinMaxFilter
            label="Cycle"
            min={cycleRange ? cycleRange.min : ""}
            max={cycleRange ? cycleRange.max : ""}
            onChange={(values) => setCycleRange(values)}
          />
          <MinMaxFilter
            label="Days in"
            min={daysRange ? daysRange.min : ""}
            max={daysRange ? daysRange.max : ""}
            onChange={(values) => setDaysRange(values)}
          />
        </div>

        <div className={s.filters_row}>
          <MinMaxFilter
            label="Total purchases (10d)"
            min={totalPurchasesRange ? totalPurchasesRange.min : ""}
            max={totalPurchasesRange ? totalPurchasesRange.max : ""}
            onChange={(values) => setTotalPurchasesRange(values)}
          />
          <MinMaxFilter
            label="Purchases 10d"
            min={purchases10Range ? purchases10Range.min : ""}
            max={purchases10Range ? purchases10Range.max : ""}
            onChange={(values) => setPurchases10Range(values)}
          />
        </div>

        <div className={s.filters_row}>
          <MinMaxFilter
            label="Ad visits (10d)"
            min={adVisitsRange ? adVisitsRange.min : ""}
            max={adVisitsRange ? adVisitsRange.max : ""}
            onChange={(values) => setAdVisitsRange(values)}
          />
          <MinMaxFilter
            label="Ad purchases (10d)"
            min={totalAdPurchasesRange ? totalAdPurchasesRange.min : ""}
            max={totalAdPurchasesRange ? totalAdPurchasesRange.max : ""}
            onChange={(values) => setTotalAdPurchasesRange(values)}
          />
        </div>

        <button className={s.clear_btn} onClick={handleClearFilters}>
          Clear Filters
        </button>
      </div>

      <Search id={adControlSearch} placeholder={t("admin.landings.search")} />
      <Table
        loading={loading}
        landingLinkByIdPath={
          mode === "courses" ? Path.landingAnalytics : Path.bookLandingAnalytics
        }
        showIndex={false}
        data={data}
        columnLabels={{
          id: "ID",
          landing_name: "Landing",
          language: "Lang",
          stage_started_at: "Start date",
          quarantine_ends_at: "End date",
          cycle_no: "Cycle",
          days_in_stage: "Days In",
          total_purchases_last_10_days: "P(10d)",
          ad_purchases_last_10_days: "AP(10d)",
          ad_visits_last_10_days: "AV(10d)",
          assignee: "Assignee",
          ad_purchases_lifetime: "AP(full)",
          total_purchases_lifetime: "P(full)",
          hours_left: "Hours left",
        }}
        structured
      />
    </div>
  );
};

export default AdControlListing;
