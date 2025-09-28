import { useState } from "react";

interface DateRange {
  startDate: string;
  endDate: string;
}

const formatDate = (d: Date) => d.toISOString().slice(0, 10);

export const DATE_RANGE_FILTER_PRESETS = [
  {
    label: "Today",
    value: "today",
    getRange: () => {
      const d = new Date();
      return [d, d] as [Date, Date];
    },
  },
  {
    label: "Yesterday",
    value: "yesterday",
    getRange: () => {
      const d = new Date();
      d.setDate(d.getDate() - 1);
      return [d, d] as [Date, Date];
    },
  },
  {
    label: "Today or Yesterday",
    value: "todayOrYesterday",
    getRange: () => {
      const today = new Date();
      const yesterday = new Date();
      yesterday.setDate(today.getDate() - 1);
      return [yesterday, today] as [Date, Date];
    },
  },
  {
    label: "Last 7 days",
    value: "last7",
    getRange: () => {
      const end = new Date();
      const start = new Date();
      start.setDate(end.getDate() - 6);
      return [start, end] as [Date, Date];
    },
  },
  {
    label: "Last 14 days",
    value: "last14",
    getRange: () => {
      const end = new Date();
      const start = new Date();
      start.setDate(end.getDate() - 13);
      return [start, end] as [Date, Date];
    },
  },
  {
    label: "Last 28 days",
    value: "last28",
    getRange: () => {
      const end = new Date();
      const start = new Date();
      start.setDate(end.getDate() - 27);
      return [start, end] as [Date, Date];
    },
  },
  {
    label: "Last 30 days",
    value: "last30",
    getRange: () => {
      const end = new Date();
      const start = new Date();
      start.setDate(end.getDate() - 29);
      return [start, end] as [Date, Date];
    },
  },
  {
    label: "This week",
    value: "thisWeek",
    getRange: () => {
      const now = new Date();
      const day = now.getDay() || 7;
      const start = new Date(now);
      start.setDate(now.getDate() - day + 1);
      const end = new Date();
      return [start, end] as [Date, Date];
    },
  },
  {
    label: "Last week",
    value: "lastWeek",
    getRange: () => {
      const now = new Date();
      const day = now.getDay() || 7;
      const end = new Date(now);
      end.setDate(now.getDate() - day);
      const start = new Date(end);
      start.setDate(end.getDate() - 6);
      return [start, end] as [Date, Date];
    },
  },
  {
    label: "This month",
    value: "thisMonth",
    getRange: () => {
      const now = new Date();
      const start = new Date(now.getFullYear(), now.getMonth(), 1);
      const end = new Date();
      return [start, end] as [Date, Date];
    },
  },
  {
    label: "Last month",
    value: "lastMonth",
    getRange: () => {
      const now = new Date();
      const start = new Date(now.getFullYear(), now.getMonth() - 1, 1);
      const end = new Date(now.getFullYear(), now.getMonth(), 0);
      return [start, end] as [Date, Date];
    },
  },
  {
    label: "Maximum",
    value: "maximum",
    getRange: () => {
      const start = new Date(2025, 2, 1);
      const end = new Date();
      return [start, end] as [Date, Date];
    },
  },
  { label: "Custom", value: "custom", getRange: null },
] as const;

export type DateRangeFilterPresetValue =
  (typeof DATE_RANGE_FILTER_PRESETS)[number]["value"];

export const useDateRangeFilter = (
  initial: DateRange | DateRangeFilterPresetValue = "custom",
) => {
  const initialPreset =
    typeof initial === "string"
      ? initial
      : ("custom" as DateRangeFilterPresetValue);

  const presetDef = DATE_RANGE_FILTER_PRESETS.find(
    (p) => p.value === initialPreset,
  );

  const initialRange = presetDef?.getRange?.()
    ? {
        startDate: formatDate(presetDef.getRange()[0]),
        endDate: formatDate(presetDef.getRange()[1]),
      }
    : typeof initial === "string"
      ? { startDate: "", endDate: "" }
      : initial;

  const [dateRange, setDateRange] = useState<DateRange>(initialRange);
  const [selectedPreset, setSelectedPreset] =
    useState<DateRangeFilterPresetValue>(initialPreset);

  const setPreset = (preset: DateRangeFilterPresetValue) => {
    setSelectedPreset(preset);
    const def = DATE_RANGE_FILTER_PRESETS.find((p) => p.value === preset);
    if (def?.getRange) {
      const [start, end] = def.getRange();
      setDateRange({ startDate: formatDate(start), endDate: formatDate(end) });
    } else {
      setDateRange({ startDate: "", endDate: "" });
    }
  };

  const handleStartDateChange = (value: string) => {
    setDateRange((prev) => ({ ...prev, startDate: value }));
    setSelectedPreset("custom");
  };

  const handleEndDateChange = (value: string) => {
    setDateRange((prev) => ({ ...prev, endDate: value }));
    setSelectedPreset("custom");
  };

  return {
    dateRange,
    selectedPreset,
    setPreset,
    handleStartDateChange,
    handleEndDateChange,
  };
};
