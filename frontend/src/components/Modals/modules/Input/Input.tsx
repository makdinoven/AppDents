import React from "react";
import s from "./Input.module.scss";
import { Trans } from "react-i18next";
import ErrorIcon from "../../../../common/Icons/ErrorIcon.tsx";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error: string | undefined;
}

const Input: React.FC<InputProps> = ({ error, ...props }) => {
  return (
    <div className={`${s.input_wrapper} ${error ? s.error : ""}`}>
      <input {...props} />
      {error && (
        <div className={s.error_icon_wrapper}>
          <ErrorIcon />
          <div className={s.tooltip}>
            <Trans i18nKey={error} />
          </div>
        </div>
      )}
    </div>
  );
};

export default Input;
