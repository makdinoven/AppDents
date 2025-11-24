import { useParams } from "react-router-dom";
import DetailHeader from "../../modules/common/DetailHeader/DetailHeader.tsx";
import { adminApi } from "../../../../../shared/api/adminApi/adminApi.ts";
import { useEffect, useState } from "react";
import {
  formatIsoToLocalDatetime,
  getFormattedDate,
  transformIdNameArrToValueNameArr,
} from "../../../../../shared/common/helpers/helpers.ts";
import DateRangeFilter from "../../../../../shared/components/ui/DateRangeFilter/DateRangeFilter.tsx";
import Loader from "../../../../../shared/components/ui/Loader/Loader.tsx";
import SwitchButtons from "../../../../../shared/components/ui/SwitchButtons/SwitchButtons.tsx";
import s from "./LandingAnalytics.module.scss";
import LandingAnalyticsChart from "../Charts/LandingAnalyticsChart.tsx";
import Table from "../../../../../shared/components/ui/Table/Table.tsx";
import { useDateRangeFilter } from "../../../../../shared/common/hooks/useDateRangeFilter.ts";
import MultiSelect from "../../../../../shared/components/MultiSelect/MultiSelect.tsx";
import LoaderOverlay from "../../../../../shared/components/ui/LoaderOverlay/LoaderOverlay.tsx";
import { Alert } from "../../../../../shared/components/ui/Alert/Alert.tsx";
import { ErrorIcon } from "../../../../../shared/assets/icons";

const LandingAnalytics = () => {
  const { id } = useParams();
  const [loading, setLoading] = useState(false);
  const [chartData, setChartData] = useState<any>(null);
  const [chartMode, setChartMode] = useState<"hour" | "day">("day");
  const [staffList, setStaffList] = useState<any>([]);
  const [accountsList, setAccountsList] = useState<any>([]);
  const [assignmentLoading, setAssignmentLoading] = useState(false);
  const [assigned, setAssigned] = useState<{
    staff: number | null;
    account: number | null;
  } | null>(null);
  const [landing, setLanding] = useState<{
    data: any;
    totals: { all: any; range: any };
    periods: { start: string; end: string }[];
  } | null>(null);
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
      landing_id: string;
      bucket: string;
      start_date?: string;
      end_date?: string;
    } = {
      landing_id: id!,
      bucket: chartMode,
    };
    if (dateRange.startDate) {
      params.start_date = dateRange.startDate;
    }
    if (dateRange.endDate) {
      params.end_date = dateRange.endDate;
    }
    try {
      const res = await adminApi.getLandingTraffic(params);

      setChartData(res.data.series);
      setLanding({
        data: res.data.landing,
        totals: { all: res.data.totals_all_time, range: res.data.totals_range },
        periods: res.data.ad_periods.map(
          (p: { start: string; end: string }) => ({
            start: formatIsoToLocalDatetime(p.start, true),
            end: formatIsoToLocalDatetime(p.end, true),
          }),
        ),
      });
      setLoading(false);
    } catch {
      Alert(`Error loading landing data`, <ErrorIcon />);
      setLoading(false);
    }
  };

  const fetchStaff = async () => {
    try {
      const res = await adminApi.getAdStaffList();
      setStaffList(transformIdNameArrToValueNameArr(res.data, false));
    } catch (error) {
      console.error(error);
    }
  };

  const fetchAccounts = async () => {
    try {
      const res = await adminApi.getAdAccountsList();
      setAccountsList(transformIdNameArrToValueNameArr(res.data, false));
    } catch (error) {
      console.error(error);
    }
  };

  const fetchAssigned = async (id: string) => {
    try {
      const res = await adminApi.getAdLandingAssigned(id);

      setAssigned({ account: res.data.account_id, staff: res.data.staff_id });
    } catch (error) {
      console.error(error);
    }
  };

  const postAssignment = async (data: {
    staff_id: number | null;
    account_id: number | null;
  }) => {
    setAssignmentLoading(true);
    try {
      await adminApi.putAdLandingAssigned(id!, data);

      await fetchAssigned(id!);
      setAssignmentLoading(false);
    } catch (error) {
      setAssignmentLoading(false);
      console.error(error);
    }
  };

  useEffect(() => {
    fetchData();
  }, [dateRange, chartMode]);

  useEffect(() => {
    if (id) {
      fetchStaff();
      fetchAccounts();
      fetchAssigned(id);
    }
  }, [id]);

  useEffect(() => {
    if (landing?.data?.created_at) {
      const createdAt = getFormattedDate(new Date(landing.data.created_at));
      const today = getFormattedDate(new Date());
      handleStartDateChange(createdAt);
      handleEndDateChange(today);
    }
  }, [landing?.data?.created_at]);

  return (
    <div className={s.landing_analytics_container}>
      <DetailHeader title={landing?.data.name} />
      {landing ? (
        <>
          <span className={s.created_at}>
            Created: {formatIsoToLocalDatetime(landing.data.created_at, true)}
          </span>
          <div className={s.filters}>
            <DateRangeFilter
              startDate={dateRange.startDate}
              endDate={dateRange.endDate}
              onEndDateChange={handleEndDateChange}
              onStartDateChange={handleStartDateChange}
              selectedPreset={selectedPreset}
              setPreset={setPreset}
            />
            <SwitchButtons
              buttonsArr={["hour", "day"]}
              activeValue={chartMode}
              handleClick={(val) => setChartMode(val)}
            />
          </div>

          {assigned && (
            <div className={s.info_container}>
              {assignmentLoading && <LoaderOverlay />}
              {staffList && (
                <div className={s.multi_select_container}>
                  <MultiSelect
                    isSearchable={false}
                    label={"Staff"}
                    id={"staff"}
                    options={staffList}
                    placeholder={"Assign staff member"}
                    selectedValue={assigned.staff ? assigned.staff : ""}
                    isMultiple={false}
                    onChange={(val) =>
                      postAssignment({
                        staff_id: val.value as unknown as number,
                        account_id: assigned.account,
                      })
                    }
                    valueKey="value"
                    labelKey="name"
                  />
                </div>
              )}
              {accountsList && (
                <div className={s.multi_select_container}>
                  <MultiSelect
                    isSearchable={false}
                    id={"accounts"}
                    label={"Ad account"}
                    options={accountsList}
                    placeholder={"Assign ad account"}
                    selectedValue={assigned.account ? assigned.account : ""}
                    isMultiple={false}
                    onChange={(val) =>
                      postAssignment({
                        staff_id: assigned.staff,
                        account_id: val.value as unknown as number,
                      })
                    }
                    valueKey="value"
                    labelKey="name"
                  />
                </div>
              )}
            </div>
          )}

          {chartData && (
            <LandingAnalyticsChart
              loading={loading}
              data={chartData}
              type={chartMode}
            />
          )}

          <div className={s.info_container}>
            <Table
              loading={loading}
              title="Range data"
              data={[
                { metric: "Purchases", value: landing.totals.range.purchases },
                { metric: "Visits", value: landing.totals.range.visits },
                {
                  metric: "Visits from ad",
                  value: landing.totals.range.ad_visits,
                },
              ]}
              columnLabels={{ metric: "Metric", value: "Value" }}
            />

            <Table
              loading={loading}
              title="All time data"
              data={[
                {
                  metric: "Conversion",
                  value: `${landing.totals.all.conversion_percent.toFixed(2)}%`,
                },
                {
                  metric: "Purchases from first visit",
                  value: landing.totals.all.purchases_first_visit,
                },
                {
                  metric: "All time purchases",
                  value: landing.totals.all.purchases,
                },
                {
                  metric: "All time visits",
                  value: landing.totals.all.visits,
                },
                {
                  metric: "Visits from ad",
                  value: landing.totals.all.ad_visits,
                },
              ]}
              columnLabels={{ metric: "Metric", value: "Value" }}
            />
          </div>

          <Table
            loading={loading}
            title="Start/End Ad"
            data={landing.periods}
            columnLabels={{ start: "Start date", end: "End date" }}
          />
        </>
      ) : (
        <Loader />
      )}
    </div>
  );
};

export default LandingAnalytics;
