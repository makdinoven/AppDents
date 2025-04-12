import React, { useState } from "react";
import s from "./ToggleCheckbox.module.scss";

interface ToggleCheckboxProps {
  isChecked?: boolean;
  onChange?: (checked: boolean) => void;
}

const ToggleCheckbox: React.FC<ToggleCheckboxProps> = ({
  isChecked = false,
  onChange,
}) => {
  const [checked, setChecked] = useState(isChecked);

  const handleChange = () => {
    const newChecked = !checked;
    setChecked(newChecked);
    onChange?.(newChecked);
  };

  return (
    <div className={s.toggleWrapper} onClick={handleChange}>
      <div className={`${s.toggle} ${checked ? s.checked : ""}`} />
    </div>
  );
};

export default ToggleCheckbox;
