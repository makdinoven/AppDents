import s from "./Search.module.scss";
import { t } from "i18next";
import { ArrowX, SearchIcon } from "../../../assets/icons";
import { useEffect, useState } from "react";
import useDebounce from "../../../common/hooks/useDebounce";

const Search = ({
  placeholder,
  onFocus,
  id = "search",
  inputRef,
  error,
  valueFromUrl = "",
  onChangeValue,
  useDebounceOnChange = false,
  debounceDelay = 400,
}: {
  id?: string;
  placeholder: string;
  onFocus?: () => void;
  inputRef?: React.RefObject<HTMLInputElement | null>;
  error?: string | null;
  valueFromUrl?: string;
  onChangeValue?: (value: string) => void;
  useDebounceOnChange?: boolean;
  debounceDelay?: number;
}) => {
  const [localValue, setLocalValue] = useState(valueFromUrl || "");
  const debouncedValue = useDebounce(localValue, debounceDelay);
  useEffect(() => {
    setLocalValue(valueFromUrl || "");
  }, [valueFromUrl]);

  useEffect(() => {
    if (!useDebounceOnChange) return;
    onChangeValue?.(debouncedValue);
  }, [debouncedValue]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newVal = e.target.value;
    setLocalValue(newVal);

    if (!useDebounceOnChange) {
      onChangeValue?.(newVal);
    }
  };

  const handleClear = () => {
    setLocalValue("");
    onChangeValue?.("");
  };

  return (
    <div
      className={`${s.input_wrapper} ${localValue ? s.filled : ""} ${error ? s.error : ""}`}
    >
      <input
        id={id}
        type="text"
        value={localValue}
        className={s.search_input}
        onChange={handleChange}
        onFocus={onFocus}
        ref={inputRef}
      />

      <div className={s.icons}>
        {localValue && (
          <span className={s.clear_icon} onClick={handleClear}>
            <ArrowX />
          </span>
        )}
        <span className={s.search_icon}>
          <SearchIcon />
        </span>
      </div>

      <label htmlFor={id} className={s.placeholder_label}>
        {!error ? t(placeholder) : error}
      </label>
    </div>
  );
};

export default Search;
