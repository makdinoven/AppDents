import s from "./Search.module.scss";
import UnstyledInput from "../../CommonComponents/UnstyledInput.tsx";
import { t } from "i18next";
import { SearchIcon } from "../../../assets/icons/index.ts";
import { useSearchParams } from "react-router-dom";
import { ArrowX } from "../../../assets/icons/index.ts";

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
  const [searchParams, setSearchParams] = useSearchParams();
  const value = searchParams.get(id) || "";

  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    const newParams = new URLSearchParams(searchParams.toString());
    if (newValue) {
      newParams.set(id, newValue);
    } else {
      newParams.delete(id);
    }
    setSearchParams(newParams, { replace: true });
  };

  const handleClear = () => {
    const newParams = new URLSearchParams(searchParams.toString());
    newParams.delete(id);
    setSearchParams(newParams, { replace: true });
  };

  return (
    <div className={`${s.input_wrapper} ${value ? s.filled : ""}`}>
      <UnstyledInput
        id={id}
        type="text"
        value={value}
        className={s.search_input}
        onChange={onChange}
        onFocus={onFocus}
        ref={inputRef}
      />
      <div className={s.icons}>
        {value && (
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
