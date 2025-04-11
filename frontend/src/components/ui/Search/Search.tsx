import s from "./Search.module.scss";
import UnstyledInput from "../../CommonComponents/UnstyledInput.tsx";
import { t } from "i18next";

const Search = ({
  placeholder,
  value,
  onChange,
  onFocus,
}: {
  placeholder: string;
  value: string;
  onFocus?: () => void;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}) => {
  return (
    <div className={s.input_wrapper}>
      <UnstyledInput
        id={"search"}
        type="text"
        value={value}
        placeholder={t(placeholder)}
        className={s.search_input}
        onChange={onChange}
        onFocus={onFocus}
      />
    </div>
  );
};

export default Search;
