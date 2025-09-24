import { useRef, useState } from "react";
import s from "./DateRangeFilter.module.scss";
import { SettingsIcon } from "../../../assets/icons";
import useOutsideClickMulti from "../../../common/hooks/useOutsideClickMulti.ts";
import {
  DATE_RANGE_FILTER_PRESETS,
  DateRangeFilterPresetValue,
} from "../../../common/hooks/useDateRangeFilter.ts";

interface DateRangeFilterProps {
  startDate: string;
  endDate: string;
  onStartDateChange: (val: string) => void;
  onEndDateChange: (val: string) => void;
  selectedPreset: DateRangeFilterPresetValue;
  setPreset: (selectedPreset: DateRangeFilterPresetValue) => void;
}

const DateRangeFilter = ({
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
  selectedPreset,
  setPreset,
}: DateRangeFilterProps) => {
  const [isPresetsOpened, setIsPresetsOpened] = useState<boolean>(false);
  const presetsContainerRef = useRef<HTMLDivElement>(null);
  const settingsButtonRef = useRef<HTMLButtonElement>(null);
  useOutsideClickMulti([presetsContainerRef, settingsButtonRef], () =>
    setIsPresetsOpened(false),
  );

  const handlePresetChange = (value: DateRangeFilterPresetValue) => {
    setPreset(value);
    setIsPresetsOpened(false);
  };

  return (
    <div className={s.wrapper}>
      <div
        ref={presetsContainerRef}
        className={`${s.presets} ${isPresetsOpened ? s.opened : ""}`}
      >
        {DATE_RANGE_FILTER_PRESETS.map((preset) => (
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
