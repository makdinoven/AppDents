import React, { useState } from "react";
import s from "./ToggleCheckbox.module.scss";

interface ToggleCheckboxProps {
  disabled?: boolean;
  variant?: "small" | "medium" | "large";
  isChecked?: boolean;
  onChange?: (checked: boolean) => void;
}

const ToggleCheckbox: React.FC<ToggleCheckboxProps> = ({
  disabled,
  variant,
  isChecked = false,
  onChange,
}) => {
  const [checked, setChecked] = useState(isChecked);

  const handleChange = () => {
    if (!disabled) {
      const newChecked = !checked;
      setChecked(newChecked);
      onChange?.(newChecked);
    }
  };

  return (
    <div
      className={`${s.toggleWrapper} ${variant ? s[variant] : ""}`}
      onClick={handleChange}
    >
      <div
        className={`${s.toggle} ${variant ? s[variant] : ""} ${checked ? s.checked : ""}`}
      />
    </div>
  );
};

export default ToggleCheckbox;
