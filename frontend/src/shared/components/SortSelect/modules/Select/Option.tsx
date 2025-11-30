import s from "./Option.module.scss";
import { t } from "i18next";

interface OptionProps<T> {
  option: T;
  radioButtonType?: "checkbox" | "radio";
  onChange: (value: string) => void;
  activeValue?: string;
}

const Option = <T extends { [key: string]: any }>({
  option,
  radioButtonType = "checkbox",
  onChange,
  activeValue,
}: OptionProps<T>) => {
  const isActive = activeValue === option.value;
  return (
    <li
      key={option.value}
      className={s.option}
      onClick={() => onChange(option.value)}
    >
      <div
        className={`${s.radio_button} ${radioButtonType === "checkbox" ? s.checkbox : s.radio} ${isActive ? s.active : ""}`}
      />
      {t(`sort.keys.${option.value}`)}
    </li>
  );
};

export default Option;
