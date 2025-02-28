import s from "./Search.module.scss";
import UnstyledInput from "../../CommonComponents/UnstyledInput.tsx";

const Search = ({
  placeholder,
  value,
  onChange,
}: {
  placeholder: string;
  value: string;
  onChange: any;
}) => {
  return (
    <div className={s.input_wrapper}>
      <UnstyledInput
        id={"search"}
        type="text"
        value={value}
        placeholder={placeholder}
        className={s.search_input}
        onChange={onChange}
      />
    </div>
  );
};

export default Search;
