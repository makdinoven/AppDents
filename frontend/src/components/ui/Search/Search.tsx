import s from "./Search.module.scss";
import UnstyledInput from "../../CommonComponents/UnstyledInput.tsx";
import { t } from "i18next";
import { SearchIcon } from "../../../assets/logos/index";

const Search = ({
  placeholder,
  value,
  onChange,
  onFocus,
  id = "search",
  inputRef,
}: {
  id?: string;
  placeholder: string;
  value: string;
  onFocus?: () => void;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  inputRef?: React.RefObject<HTMLInputElement | null>;
}) => {
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
      <span className={s.search_icon}>
        <SearchIcon />
      </span>
      <label htmlFor={id} className={s.placeholder_label}>
        {t(placeholder)}
      </label>
    </div>
  );
};

export default Search;
