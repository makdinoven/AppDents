import s from "./MinMaxFilter.module.scss";
import { useEffect, useRef, useState } from "react";
import useDebounce from "../../../common/hooks/useDebounce.ts";
import RangeFilterItem from "../../filters/RangeFilter/RangeFilterItem/RangeFilterItem.tsx";

interface MinMaxFilterProps {
  label?: string;
  min: string | "";
  max: string | "";
  onChange: (values: { min: string | ""; max: string | "" }) => void;
  placeholderMin?: string;
  placeholderMax?: string;
}

const MinMaxFilter = ({
  label,
  min,
  max,
  onChange,
  placeholderMin = "min",
  placeholderMax = "max",
}: MinMaxFilterProps) => {
  const [localMin, setLocalMin] = useState(min);
  const [localMax, setLocalMax] = useState(max);
  const isManualChange = useRef(true);
  const debouncedMin = useDebounce(localMin, 500);
  const debouncedMax = useDebounce(localMax, 500);

  useEffect(() => {
    if (isManualChange.current) {
      onChange({ min: debouncedMin, max: debouncedMax });
    }
    isManualChange.current = true;
  }, [debouncedMin, debouncedMax]);

  const handleClear = () => {
    isManualChange.current = false;
    setLocalMin("");
    setLocalMax("");
    onChange({ min: "", max: "" });
  };

  const handleSync = () => {
    isManualChange.current = false;
    if (localMin) {
      setLocalMax(localMin);
      onChange({ min: localMin, max: localMin });
    } else if (localMax) {
      setLocalMin(localMax);
      onChange({ min: localMax, max: localMax });
    }
  };

  const showBtns = localMin || localMax;

  const minNumber = localMin ? parseInt(localMin, 10) : 0;
  const maxNumber = localMax ? parseInt(localMax, 10) : 0;

  return (
    <div className={s.filter_container}>
      <div className={s.filter_header}>
        {label && <span className={s.label}>{label}</span>}
        <div className={s.btns}>
          <button
            type="button"
            onClick={handleSync}
            className={`${s.sync_btn} ${showBtns ? s.show : ""}`}
          >
            sync
          </button>
          <button
            type="button"
            onClick={handleClear}
            className={`${s.clear_btn} ${showBtns ? s.show : ""}`}
          >
            clear
          </button>
        </div>
      </div>

      <div className={s.inputs}>
        <div className={s.input_wrapper}>
          <RangeFilterItem
            id="min"
            min="0"
            max={localMax || ""}
            placeholder={placeholderMin}
            value={localMin}
            disabledMinus={minNumber <= 0}
            disabledPlus={false}
            actions={{
              change: (v) => setLocalMin(v),
              dec: () => {
                const current = localMin ? parseInt(localMin, 10) : 0;
                const next = Math.max(current - 1, 0);
                setLocalMin(next === 0 ? "" : String(next));
              },
              inc: () => {
                const current = localMin ? parseInt(localMin, 10) : 0;
                const next = current + 1;
                setLocalMin(String(next));
              },
            }}
          />
        </div>

        <span className={s.dash}>—</span>

        <div className={s.input_wrapper}>
          <RangeFilterItem
            id="max"
            min={localMin || "0"}
            max=""
            placeholder={placeholderMax}
            value={localMax}
            disabledMinus={maxNumber <= 0}
            disabledPlus={false}
            actions={{
              change: (v) => setLocalMax(v),
              dec: () => {
                const current = localMax ? parseInt(localMax, 10) : 0;
                const next = Math.max(current - 1, 0);
                setLocalMax(next === 0 ? "" : String(next));
              },
              inc: () => {
                const current = localMax ? parseInt(localMax, 10) : 0;
                const next = current + 1;
                setLocalMax(String(next));
              },
            }}
          />
        </div>
      </div>
    </div>
  );
};

export default MinMaxFilter;
