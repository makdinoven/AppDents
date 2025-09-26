import React from "react";
import s from "./AdminField.module.scss";
import { Trans } from "react-i18next";

interface FieldProps {
  id: string;
  type: "textarea" | "input" | "date";
  value?: string | number;
  onChange: (value: string) => void;
  onBlur?: any;
  inputType?: string;
  label?: React.ReactNode;
  error?: string;
  placeholder?: string;
  className?: string;
}

const AdminField: React.FC<FieldProps> = ({
  placeholder,
  className,
  id,
  type,
  value,
  onChange,
  onBlur,
  label,
  error,
  inputType,
  ...props
}) => {
  const handleChange = (e: any) => {
    onChange(e.target);
  };

  return (
    <div
      className={`${s.field_wrapper} ${error ? s.error : ""} ${className ? className : ""}`}
    >
      {label && <label htmlFor={id}>{label}</label>}

      {type === "textarea" ? (
        <textarea
          placeholder={placeholder}
          id={id}
          name={id}
          value={value}
          onChange={handleChange}
          onBlur={onBlur}
          {...props}
          className={s.textarea}
        />
      ) : (
        <input
          placeholder={placeholder}
          type={inputType}
          id={id}
          name={id}
          value={value}
          className={s.input}
          onChange={handleChange}
          onBlur={onBlur}
          {...props}
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
