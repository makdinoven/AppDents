import React from "react";
import s from "./Checkbox.module.scss";
import { CheckboxBody, CheckboxCheckMark } from "../../../assets/icons";

interface CheckboxProps {
  disabled?: boolean;
  isChecked?: boolean;
  onChange?: (checked: boolean) => void;
  className?: string;
}

const Checkbox: React.FC<CheckboxProps> = ({
  disabled = false,
  isChecked = false,
  onChange,
}) => {
  const handleChange = () => {
    if (!disabled) {
      onChange?.(!isChecked);
    }
  };

  return (
    <span
      onClick={handleChange}
      className={`${s.checkbox} ${isChecked ? s.checked : ""} ${disabled ? s.disabled : ""}`}
    >
      <CheckboxCheckMark className={s.check_mark} />
      <CheckboxBody className={s.checkbox_body} />
    </span>
  );
};

export default Checkbox;
