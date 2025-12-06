import s from "./Option.module.scss";
import { Trans } from "react-i18next";

interface OptionProps<T> {
  option: T;
  radioButtonType?: "checkbox" | "radio";
  onChange: (value?: string) => void;
  isActive?: boolean;
  allowUncheck?: boolean;
}

const Option = <T extends { [key: string]: any }>({
  option,
  radioButtonType = "checkbox",
  onChange,
  allowUncheck,
  isActive,
}: OptionProps<T>) => {
  return (
    <li
      key={option.value}
      className={s.option}
      onClick={() =>
        isActive
          ? allowUncheck
            ? onChange(undefined)
            : undefined
          : onChange(option.value)
      }
    >
      <div
        className={`${s.radio_button} ${radioButtonType === "checkbox" ? s.checkbox : s.radio} ${isActive ? s.active : ""}`}
      />
      {<Trans i18nKey={option.label} />}
      {typeof option.count !== "undefined" && (
        <span className={`${s.count} ${option.count === 0 ? s.inactive : ""}`}>
          {option.count}
        </span>
      )}
    </li>
  );
};

export default Option;
