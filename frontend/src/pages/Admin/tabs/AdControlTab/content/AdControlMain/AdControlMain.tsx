import s from "./AdControlMain.module.scss";
import DateRangeFilter from "../../../../../../components/ui/DateRangeFilter/DateRangeFilter.tsx";
import MultiSelect from "../../../../../../components/CommonComponents/MultiSelect/MultiSelect.tsx";
import { LANGUAGES_NAME } from "../../../../../../common/helpers/commonConstants.ts";
import SwitchButtons from "../../../../../../components/ui/SwitchButtons/SwitchButtons.tsx";
import SortOrderToggle, {
  SortDirectionType,
} from "../../../../../../components/ui/SortOrderToggle/SortOrderToggle.tsx";
import MinMaxFilter from "../../../../../../components/ui/MinMaxFilter/MinMaxFilter.tsx";
import Search from "../../../../../../components/ui/Search/Search.tsx";
import { t } from "i18next";
import Table from "../../../../../../components/ui/Table/Table.tsx";
import { Path } from "../../../../../../routes/routes.ts";
import Loader from "../../../../../../components/ui/Loader/Loader.tsx";
import { useSearchParams } from "react-router-dom";
import { useEffect, useState } from "react";
import useDebounce from "../../../../../../common/hooks/useDebounce.ts";
import { useDateRangeFilter } from "../../../../../../common/hooks/useDateRangeFilter.ts";
import { adminApi } from "../../../../../../api/adminApi/adminApi.ts";
import { Alert } from "../../../../../../components/ui/Alert/Alert.tsx";
import { ErrorIcon } from "../../../../../../assets/icons";
import { transformIdNameArrToValueNameArr } from "../../../../../../common/helpers/helpers.ts";

const adControlSearch = "ad-control-q";

type ColorType = "green" | "orange" | "red" | "white";

const AdControlMain = () => {
  const [searchParams] = useSearchParams();
  const [mode, setMode] = useState<"quarantine" | "observation">("quarantine");
  const [loading, setLoading] = useState<boolean>(false);
  const [language, setLanguage] = useState<string>("EN");
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
  const [purchasesFirst5Range, setPurchasesFirst5Range] = useState<{
    min: string;
    max: string;
  } | null>(null);
  const [purchasesLast10Range, setPurchasesLast10Range] = useState<{
    min: string;
    max: string;
  } | null>(null);
  const [sortBy, setSortBy] = useState("");
  const [staffList, setStaffList] = useState<any>([]);
  const [accountsList, setAccountsList] = useState<any>([]);
  const isQuarantine = mode === "quarantine";
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
      start_date?: string;
      end_date?: string;
      language?: string;
      sort_dir?: SortDirectionType;
      colors?: ColorType[];
      cycle_min?: number;
      cycle_max?: number;
      first5_min?: number;
      first5_max?: number;
      sales10_min?: number;
      sales10_max?: number;
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
      params.start_date = dateRange.startDate;
    }
    if (dateRange.endDate) {
      params.end_date = dateRange.endDate;
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
    if (purchasesLast10Range) {
      if (purchasesLast10Range.min && !isQuarantine) {
        params.sales10_min = Number(purchasesLast10Range.min);
      }
      if (purchasesLast10Range.max && !isQuarantine) {
        params.sales10_max = Number(purchasesLast10Range.max);
      }
    }
    if (purchasesFirst5Range) {
      if (purchasesFirst5Range.min && isQuarantine) {
        params.first5_min = Number(purchasesFirst5Range.min);
      }
      if (purchasesFirst5Range.max && isQuarantine) {
        params.first5_min = Number(purchasesFirst5Range.max);
      }
    }

    if (sortBy && sortBy !== "all") {
      if (
        (isQuarantine && (sortBy === "deadline" || sortBy === "first5")) ||
        (!isQuarantine && sortBy === "sales10") ||
        ["days", "cycle", "name", "language", "stage_start", "color"].includes(
          sortBy,
        )
      ) {
        params.sort_by = sortBy;
      }
    }
    if (selectedStaff && selectedStaff !== "all") {
      params.staff_id = selectedStaff;
    }
    if (selectedAccount && selectedAccount !== "all") {
      params.account_id = selectedAccount;
    }
    try {
      if (mode === "quarantine") {
        const res = await adminApi.getAdListQuarantine(params);
        setData(res.data.items);
      } else {
        const res = await adminApi.getAdListObservation(params);
        setData(res.data.items);
      }

      setLoading(false);
    } catch (err) {
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
    mode,
    debauncedSearchQuery,
    dateRange,
    language,
    sortOrder,
    colors,
    cycleRange?.min,
    cycleRange?.max,
    daysRange?.min,
    daysRange?.max,
    purchasesFirst5Range?.min,
    purchasesFirst5Range?.max,
    purchasesLast10Range?.min,
    purchasesLast10Range?.max,
    sortBy,
    selectedStaff,
    selectedAccount,
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
    setPurchasesFirst5Range(null);
    setPurchasesLast10Range(null);
    setDaysRange(null);
    setSortBy("");
    setLanguage("EN");
    setSelectedAccount("all");
    setSelectedStaff("all");
  };

  return !data && loading ? (
    <Loader />
  ) : (
    <>
      <div className={s.filters}>
        <div className={s.top_filters}>
          <DateRangeFilter
            startDate={dateRange.startDate}
            endDate={dateRange.endDate}
            onEndDateChange={handleEndDateChange}
            onStartDateChange={handleStartDateChange}
            selectedPreset={selectedPreset}
            setPreset={setPreset}
          />

          <div className={s.filters_col}>
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
              ]}
              placeholder={"Choose a color"}
              selectedValue={colors}
              isMultiple={true}
              onChange={(val) => setColors(val.value as ColorType[])}
              valueKey="value"
              labelKey="name"
            />
          </div>
          <div className={s.filters_col}>
            <SwitchButtons
              buttonsArr={["quarantine", "observation"]}
              activeValue={mode}
              handleClick={(val) => setMode(val)}
            />
          </div>
        </div>
        <div className={s.top_filters}>
          <div className={s.sort_filters}>
            <MultiSelect
              isSearchable={false}
              id={"sort_by"}
              label={"Sort by"}
              options={[
                { name: "All", value: "all" },
                ...(isQuarantine
                  ? [
                      { name: "Deadline", value: "deadline" },
                      { name: "Purchases (first 5d)", value: "first5" },
                    ]
                  : [{ name: "Purchases (last 10d)", value: "sales10" }]),
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

        <div className={s.min_max_filters_container}>
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
          {isQuarantine ? (
            <MinMaxFilter
              label="Purchases (first 5d)"
              min={purchasesFirst5Range ? purchasesFirst5Range.min : ""}
              max={purchasesFirst5Range ? purchasesFirst5Range.max : ""}
              onChange={(values) => setPurchasesFirst5Range(values)}
            />
          ) : (
            <MinMaxFilter
              label="Purchases (last 10d)"
              min={purchasesLast10Range ? purchasesLast10Range.min : ""}
              max={purchasesLast10Range ? purchasesLast10Range.max : ""}
              onChange={(values) => setPurchasesLast10Range(values)}
            />
          )}
        </div>
        <button className={s.clear_btn} onClick={handleClearFilters}>
          Clear Filters
        </button>
      </div>

      <div className={s.table_container}>
        <Search id={adControlSearch} placeholder={t("admin.landings.search")} />
        <Table
          loading={loading}
          landingLinkByIdPath={Path.landingAnalytics}
          data={data}
          columnLabels={{
            id: "ID",
            landing_name: "Landing",
            language: "Lang",
            stage_started_at: "Start date",
            quarantine_ends_at: "End date",
            cycle_no: "Cycle",
            days_in_stage: "Days In ",
            ad_purchases_first_5_days: "Purchases(5d)",
            ad_purchases_last_10_days: "Purchases(10d)",
            assignee: "Assignee",
          }}
        />
      </div>
    </>
  );
};

export default AdControlMain;
