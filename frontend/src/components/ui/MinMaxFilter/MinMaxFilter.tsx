import s from "./MinMaxFilter.module.scss";
import { useEffect, useRef, useState } from "react";
import useDebounce from "../../../common/hooks/useDebounce.ts";

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

  const handleStep = (field: "min" | "max", delta: number) => {
    const currentStr = field === "min" ? localMin : localMax;
    const currentNum = currentStr ? parseInt(currentStr, 10) : 0;
    let newValue = currentNum + delta;
    if (newValue <= 0) newValue = 0;
    const newStr = newValue === 0 ? "" : String(newValue);

    if (field === "min") {
      setLocalMin(newStr);
    } else {
      setLocalMax(newStr);
    }
  };

  const renderPlusMinusBtns = (field: "min" | "max") => (
    <div className={s.plus_minus_btns}>
      <button
        type="button"
        onClick={() => handleStep(field, 1)}
        className={s.plus}
      >
        +
      </button>
      <button
        type="button"
        onClick={() => handleStep(field, -1)}
        className={s.minus}
      >
        –
      </button>
    </div>
  );

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
          <input
            type="number"
            value={localMin}
            placeholder={placeholderMin}
            onChange={(e) => setLocalMin(e.target.value)}
            className={s.input}
          />
          {renderPlusMinusBtns("min")}
        </div>

        <span className={s.dash}>—</span>

        <div className={s.input_wrapper}>
          <input
            type="number"
            value={localMax}
            placeholder={placeholderMax}
            onChange={(e) => setLocalMax(e.target.value)}
            className={s.input}
          />
          {renderPlusMinusBtns("max")}
        </div>
      </div>
    </div>
  );
};

export default MinMaxFilter;
