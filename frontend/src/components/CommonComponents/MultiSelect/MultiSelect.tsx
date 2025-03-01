import s from "./MultiSelect.module.scss";
import Select from "react-select";
import { t } from "i18next";

interface MultiSelectProps<T> {
  id: string;
  options: T[];
  placeholder: string;
  label: string;
  isMultiple: boolean;
  selectedValue: string | number | string[];
  onChange: (e: { name: string; value: string | string[] }) => void;
  valueKey: keyof T;
  labelKey: keyof T;
}

const customStyles = {
  placeholder: (provided: any) => ({
    ...provided,
    color: "#5B6968",
  }),
  singleValue: (provided: any) => ({
    ...provided,
    color: "#01433D",
  }),
  container: (provided: any) => ({
    ...provided,
    height: "100%",
    color: "#01433D",
    "&:active": { borderColor: "#7FDFD5" },
    "&:focus": { borderColor: "#7FDFD5" },
  }),
  control: (provided: any, state: any) => ({
    ...provided,
    padding: "0",
    height: "100%",
    flex: "1",
    cursor: "pointer",
    borderRadius: "10px",
    color: "#01433D",
    borderColor: state.isFocused ? "##01433D" : "#01433D",
    backgroundColor: "transparent",
    transition: "all 0.15s ease-in-out",
    boxShadow: state.isFocused ? "none" : provided.boxShadow,
    "&:hover": { borderColor: "#01433D" },
    "&:focus": {
      borderColor: "#01433D",
      outline: "2px solid #01433D",
      boxShadow: "none",
    },
    "&:active": {
      borderColor: "#01433D",
      outline: "2px solid #01433D",
      boxShadow: "none",
    },
  }),
  menu: (provided: any) => ({
    ...provided,
    backgroundColor: "#EDF8FF",
    outline: "none",
    boxShadow: "none",
    border: "1px solid rgba(1,67,61,0.4)",
    padding: "0px 5px",
    borderRadius: "10px",
  }),
  option: (provided: any, state: any) => ({
    ...provided,
    cursor: "pointer",
    backgroundColor: state.isSelected ? "#7FDFD5" : "#EDF8FF",
    color: state.isSelected ? "#EDF8FF" : "#01433D",
    margin: "4px 0",
    borderRadius: "10px",
    transition: "all 0.15s ease-in-out",
    "&:hover": state.isSelected
      ? { backgroundColor: "#7FDFD5", color: "#EDF8FF" }
      : { backgroundColor: "#01433D", color: "#EDF8FF" },
  }),
  multiValue: (provided: any) => ({
    ...provided,
    backgroundColor: "#7FDFD5",
    color: "#EDF8FF",
    borderRadius: "5px",
    borderColor: "#01433D",
  }),
  multiValueLabel: (provided: any) => ({
    ...provided,
    color: "#EDF8FF",
  }),
  multiValueRemove: (provided: any) => ({
    ...provided,
    color: "#EDF8FF",
    transition: "all 0.15s ease-in-out",
    "&:hover": { backgroundColor: "#ff5c20", color: "#EDF8FF" },
  }),
};

const MultiSelect = <T extends { [key: string]: any }>({
  id,
  options,
  placeholder,
  label,
  isMultiple,
  selectedValue,
  onChange,
  valueKey,
  labelKey,
}: MultiSelectProps<T>) => {
  const formattedOptions = options.map((option) => ({
    value: option[valueKey] as string,
    label: option[labelKey] as string,
  }));

  const selectedOption = isMultiple
    ? formattedOptions.filter((option) =>
        (selectedValue as string[])?.includes(option.value),
      )
    : formattedOptions.find((option) => option.value === selectedValue) || null;

  return (
    <div className={s.multi_select}>
      <label htmlFor={id}>{label}</label>
      <Select
        id={id}
        name={id}
        isMulti={isMultiple}
        options={formattedOptions}
        value={selectedOption}
        onChange={(selected) => {
          const value = isMultiple
            ? (selected as { value: string; label: string }[]).map(
                (item) => item.value,
              )
            : (selected as { value: string; label: string })?.value || "";
          onChange({ name: id, value });
        }}
        placeholder={placeholder}
        noOptionsMessage={() => t("nothingFound")}
        styles={customStyles}
      />
    </div>
  );
};

export default MultiSelect;
