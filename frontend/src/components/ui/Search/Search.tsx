import s from "./Search.module.scss";
import UnstyledInput from "../../CommonComponents/UnstyledInput.tsx";
import { t } from "i18next";

const Search = ({
  placeholder,
  value,
  onChange,
  onFocus,
  id = "search",
  inputRef,
}: {
  id: string;
  placeholder: string;
  value: string;
  onFocus?: () => void;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  inputRef?: React.RefObject<HTMLInputElement | null>;
}) => {
  return (
    <div className={s.input_wrapper}>
      <UnstyledInput
        id={id}
        type="text"
        value={value}
        placeholder={t(placeholder)}
        className={s.search_input}
        onChange={onChange}
        onFocus={onFocus}
        ref={inputRef}
      />
    </div>
  );
};

export default Search;
