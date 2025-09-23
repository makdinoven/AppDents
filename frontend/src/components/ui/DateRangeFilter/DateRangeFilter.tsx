import { useRef, useState } from "react";
import s from "./DateRangeFilter.module.scss";
import { SettingsIcon } from "../../../assets/icons";
import useOutsideClickMulti from "../../../common/hooks/useOutsideClickMulti.ts";

interface DateRangeFilterProps {
  startDate: string;
  endDate: string;
  onStartDateChange: (val: string) => void;
  onEndDateChange: (val: string) => void;
}

const presets = [
  {
    label: "Today",
    value: "today",
    getRange: () => {
      const d = new Date();
      return [d, d];
    },
  },
  {
    label: "Yesterday",
    value: "yesterday",
    getRange: () => {
      const d = new Date();
      d.setDate(d.getDate() - 1);
      return [d, d];
    },
  },
  {
    label: "Today or Yesterday",
    value: "todayOrYesterday",
    getRange: () => {
      const today = new Date();
      const yesterday = new Date();
      yesterday.setDate(today.getDate() - 1);
      return [yesterday, today];
    },
  },
  {
    label: "Last 7 days",
    value: "last7",
    getRange: () => {
      const end = new Date();
      const start = new Date();
      start.setDate(end.getDate() - 6);
      return [start, end];
    },
  },
  {
    label: "Last 14 days",
    value: "last14",
    getRange: () => {
      const end = new Date();
      const start = new Date();
      start.setDate(end.getDate() - 13);
      return [start, end];
    },
  },
  {
    label: "Last 28 days",
    value: "last28",
    getRange: () => {
      const end = new Date();
      const start = new Date();
      start.setDate(end.getDate() - 27);
      return [start, end];
    },
  },
  {
    label: "Last 30 days",
    value: "last30",
    getRange: () => {
      const end = new Date();
      const start = new Date();
      start.setDate(end.getDate() - 29);
      return [start, end];
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
      return [start, end];
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
      return [start, end];
    },
  },
  {
    label: "This month",
    value: "thisMonth",
    getRange: () => {
      const now = new Date();
      const start = new Date(now.getFullYear(), now.getMonth(), 1);
      const end = new Date();
      return [start, end];
    },
  },
  {
    label: "Last month",
    value: "lastMonth",
    getRange: () => {
      const now = new Date();
      const start = new Date(now.getFullYear(), now.getMonth() - 1, 1);
      const end = new Date(now.getFullYear(), now.getMonth(), 0);
      return [start, end];
    },
  },
  {
    label: "Custom",
    value: "custom",
    getRange: null,
  },
];

const formatDate = (d: Date) => d.toISOString().slice(0, 10);

const DateRangeFilter = ({
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
}: DateRangeFilterProps) => {
  const [selectedPreset, setSelectedPreset] = useState<string>("custom");
  const [isPresetsOpened, setIsPresetsOpened] = useState<boolean>(false);
  const presetsContainerRef = useRef<HTMLDivElement>(null);
  const settingsButtonRef = useRef<HTMLButtonElement>(null);
  useOutsideClickMulti([presetsContainerRef, settingsButtonRef], () =>
    setIsPresetsOpened(false),
  );

  const handlePresetChange = (value: string) => {
    setSelectedPreset(value);
    const preset = presets.find((p) => p.value === value);
    if (preset?.getRange) {
      const [start, end] = preset.getRange();
      onStartDateChange(formatDate(start));
      onEndDateChange(formatDate(end));
    } else {
      onStartDateChange("");
      onEndDateChange("");
    }
    setIsPresetsOpened(false);
  };

  return (
    <div className={s.wrapper}>
      <div
        ref={presetsContainerRef}
        className={`${s.presets} ${isPresetsOpened ? s.opened : ""}`}
      >
        {presets.map((preset) => (
          <label
            key={preset.value}
            className={`${s.preset} ${preset.value === selectedPreset ? s.selected : ""}`}
          >
            <input
              type="radio"
              name="dateRange"
              value={preset.value}
              checked={selectedPreset === preset.value}
              onChange={() => handlePresetChange(preset.value)}
            />
            {preset.label}
            <span
              className={`${s.radio_circle} ${preset.value === selectedPreset ? s.active : ""}`}
            ></span>
          </label>
        ))}
      </div>

      <button
        ref={settingsButtonRef}
        onClick={() => setIsPresetsOpened(!isPresetsOpened)}
        className={`${s.settings_btn} ${isPresetsOpened ? s.active : ""}`}
      >
        <SettingsIcon />
      </button>

      <div className={s.input_wrapper}>
        <label>Start date</label>
        <input
          id="start_date"
          type="date"
          value={startDate}
          onChange={(e) => onStartDateChange(e.target.value)}
          className={s.date_input}
        />
      </div>
      <div className={s.input_wrapper}>
        <label>End date</label>
        <input
          id="end_date"
          type="date"
          value={endDate}
          onChange={(e) => onEndDateChange(e.target.value)}
          className={s.date_input}
        />
      </div>
    </div>
  );
};

export default DateRangeFilter;
