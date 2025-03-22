import React from "react";
import s from "./Input.module.scss";
import { Trans } from "react-i18next";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error: string | undefined;
}

const Input: React.FC<InputProps> = ({ error, ...props }) => {
  return (
    <div className={`${s.input_wrapper} ${error ? s.error : ""}`}>
      <input {...props} />
      {error && (
        <span className={s.error_message}>
          <Trans i18nKey={error} />
        </span>
      )}
    </div>
  );
};

export default Input;
