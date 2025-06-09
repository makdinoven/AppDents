import s from "./MultiSelect.module.scss";
import Select from "react-select";
import { t } from "i18next";

interface MultiSelectProps<T> {
  id: string;
  options: T[];
  placeholder: string;
  label?: string;
  isMultiple: boolean;
  selectedValue: string | number | string[];
  onChange: (e: { name: string; value: string | string[] }) => void;
  valueKey: keyof T;
  labelKey: keyof T;
  isSearchable?: boolean;
  isWider?: boolean;
}

const HOVER_COLOR = "rgba(100, 116, 139, 0.1)";
const PRIMARY_COLOR = "#7FDFD5";
const ACCENT_COLOR = "#01433D";
const BACKGROUND_COLOR = "#EDF8FF";

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
  isSearchable,
  isWider = false,
}: MultiSelectProps<T>) => {
  const customStyles = {
    placeholder: (provided: any) => ({
      ...provided,
      color: "#5B6968",
    }),
    singleValue: (provided: any) => ({
      ...provided,
      margin: 0,
      color: "unset",
      // fontSize: "24px",
    }),
    indicatorSeparator: (provided: any) => ({
      ...provided,
      display: "none",
    }),
    indicatorsContainer: (provided: any) => ({
      ...provided,
      padding: "0",
      position: "absolute",
      right: 0,
      top: "50%",
      transform: "translateY(-50%)",
      "& svg path": {
        fill: "#5b6968",
      },
    }),
    // container: (provided: any) => ({
    //   ...provided,
    //   height: "100%",
    // }),
    control: (provided: any, state: any) => ({
      ...provided,
      padding: "0 15px",
      paddingRight: "40px",
      height: "100%",
      flex: "1",
      cursor: "pointer",
      border: `2px solid ${HOVER_COLOR}`,
      borderRadius: "15px",
      color: ACCENT_COLOR,
      borderColor: HOVER_COLOR,
      backgroundColor: state.isFocused ? HOVER_COLOR : "transparent",
      transition: "all 0.15s ease-in-out",
      boxShadow: state.isFocused ? "none" : provided.boxShadow,
      "&:hover": {
        borderColor: HOVER_COLOR,
        color: ACCENT_COLOR,
        backgroundColor: HOVER_COLOR,
      },
      "&:focus": {
        color: ACCENT_COLOR,
      },
      "&:active": {
        color: ACCENT_COLOR,
      },
    }),
    menu: (provided: any) => ({
      ...provided,
      backgroundColor: BACKGROUND_COLOR,
      left: isWider ? "50%" : "",
      transform: isWider ? "translateX(-50%)" : "",
      width: isWider ? "120%" : "100%",
      outline: "none",
      border: `2px solid ${HOVER_COLOR}`,
      padding: "10px",
      borderRadius: "15px",
      boxShadow: "0 4px 8px rgba(1, 67, 61, 0.1)",
      zIndex: 9999,
    }),
    menuList: (provided: any) => ({
      ...provided,
      padding: "0",
      display: "flex",
      flexDirection: "column",
      gap: "5px",
    }),
    option: (provided: any, state: any) => ({
      ...provided,
      cursor: "pointer",
      backgroundColor: state.isSelected ? PRIMARY_COLOR : BACKGROUND_COLOR,
      color: state.isSelected ? BACKGROUND_COLOR : ACCENT_COLOR,
      padding: "2px 10px",
      borderRadius: "15px",
      transition: "all 0.15s ease-in-out",
      "&:hover": state.isSelected
        ? { backgroundColor: PRIMARY_COLOR, color: BACKGROUND_COLOR }
        : { backgroundColor: HOVER_COLOR, color: ACCENT_COLOR },
    }),
    multiValue: (provided: any) => ({
      ...provided,
      backgroundColor: PRIMARY_COLOR,
      color: BACKGROUND_COLOR,
      borderRadius: "10px",
      borderColor: ACCENT_COLOR,
    }),
    multiValueLabel: (provided: any) => ({
      ...provided,
      color: BACKGROUND_COLOR,
    }),
    multiValueRemove: (provided: any) => ({
      ...provided,
      color: BACKGROUND_COLOR,
      transition: "all 0.15s ease-in-out",
      "&:hover": { backgroundColor: "#ff5c20", color: BACKGROUND_COLOR },
    }),
  };

  const formattedOptions = options.map((option) => ({
    value: option[valueKey] as string,
    label: t(option[labelKey]) as string,
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
        isSearchable={isSearchable}
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
