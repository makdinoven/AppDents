import s from "./Option.module.scss";
import { Trans } from "react-i18next";
import { CheckMark } from "../../../assets/icons";

interface OptionProps<T> {
  option: T;
  radioButtonType?: "checkbox" | "radio";
  onChange: (value?: string) => void;
  isActive?: boolean;
  allowUncheck?: boolean;
  className?: string;
  activeClassName?: string;
}

const Option = <T extends { [key: string]: any }>({
  option,
  radioButtonType = "checkbox",
  onChange,
  allowUncheck,
  isActive,
  className,
  activeClassName,
}: OptionProps<T>) => {
  const isCheckbox = radioButtonType === "checkbox";
  return (
    <li
      key={option.value}
      className={`${s.option} ${className ? className : ""}`}
      onClick={() =>
        isActive
          ? allowUncheck
            ? onChange(undefined)
            : undefined
          : onChange(option.value)
      }
    >
      <div
        className={`${s.radio_button} ${!isCheckbox ? s.radio : ""} ${isActive ? (activeClassName ? activeClassName : s.active) : ""}`}
      >
        {isCheckbox && isActive && <CheckMark />}
      </div>
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
