import React from "react";
import s from "./AdminField.module.scss";
import { Trans } from "react-i18next";

interface FieldProps {
  id: string;
  type: "textarea" | "input";
  value?: string | number;
  onChange: (value: string) => void;
  inputType?: string;
  label?: React.ReactNode;
  error?: string;
}

const AdminField: React.FC<FieldProps> = ({
  id,
  type,
  value,
  onChange,
  label,
  error,
  inputType,
  ...props
}) => {
  const handleChange = (e: any) => {
    onChange(e.target);
  };

  return (
    <div className={`${s.field_wrapper} ${error ? s.error : ""}`}>
      {label && <label htmlFor={id}>{label}</label>}

      {type === "textarea" ? (
        <textarea
          id={id}
          name={id}
          value={value}
          onChange={handleChange}
          {...props}
          className={s.textarea}
        />
      ) : (
        <input
          type={inputType}
          id={id}
          name={id}
          value={value}
          onChange={handleChange}
          {...props}
          className={s.input}
        />
      )}

      {error && (
        <span className={s.error_message}>
          <Trans i18nKey={error} />
        </span>
      )}
    </div>
  );
};

export default AdminField;
