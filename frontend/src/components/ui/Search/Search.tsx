import s from "./Search.module.scss";
import { t } from "i18next";
import { ArrowX, SearchIcon } from "../../../assets/icons/index.ts";
import { useLocation, useSearchParams } from "react-router-dom";
import { useEffect, useState } from "react";

const Search = ({
  placeholder,
  onFocus,
  id = "search",
  inputRef,
}: {
  id?: string;
  placeholder: string;
  onFocus?: () => void;
  inputRef?: React.RefObject<HTMLInputElement | null>;
}) => {
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const [localValue, setLocalValue] = useState(searchParams.get(id) || "");

  useEffect(() => {
    const currentValue = searchParams.get(id) || "";
    setLocalValue(currentValue);
  }, [searchParams, id]);

  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setLocalValue(newValue);

    const newParams = new URLSearchParams(searchParams.toString());
    if (newValue) {
      newParams.set(id, newValue);
    } else {
      newParams.delete(id);
    }
    setSearchParams(newParams, {
      replace: true,
      ...(location.state?.backgroundLocation
        ? { state: { backgroundLocation: location.state.backgroundLocation } }
        : {}),
    });
  };

  const handleClear = () => {
    setLocalValue("");
    const newParams = new URLSearchParams(searchParams.toString());
    newParams.delete(id);
    setSearchParams(newParams, {
      replace: true,
      ...(location.state?.backgroundLocation
        ? { state: { backgroundLocation: location.state.backgroundLocation } }
        : {}),
    });
  };

  return (
    <div className={`${s.input_wrapper} ${localValue ? s.filled : ""}`}>
      <input
        id={id}
        type="text"
        value={localValue}
        className={s.search_input}
        onChange={onChange}
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
        {t(placeholder)}
      </label>
    </div>
  );
};

export default Search;
