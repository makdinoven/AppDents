import React, { ReactNode, useState } from "react";
import s from "./Input.module.scss";
import { Trans } from "react-i18next";
import { EyeClosed, EyeOpened, ErrorIcon } from "../../../../assets/icons";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  currentIndicator?: ReactNode | null;
}

const Input: React.FC<InputProps> = ({ error, type, ...props }) => {
  const { currentIndicator, ...rest } = props;
  const [visible, setVisible] = useState(false);
  const isPassword = type === "password";

  const inputType = isPassword ? (visible ? "text" : "password") : type;

  return (
    <div
      style={{ paddingRight: `${isPassword && error ? "65px" : ""}` }}
      className={`${s.input_wrapper} ${error ? s.error : ""}`}
    >
      <input {...props} type={inputType} />

      {currentIndicator && (
        <div className={s.error_icon_wrapper}>
          {currentIndicator}
          <div className={s.tooltip}>
            <Trans i18nKey={error} />
          </div>
        </div>
      )}

      {isPassword && (
        <button
          style={{ right: `${error ? "35px" : "0"}` }}
          type="button"
          className={s.eye}
          onClick={() => setVisible((prev) => !prev)}
          tabIndex={-1}
        >
          {visible ? <EyeClosed /> : <EyeOpened />}
        </button>
      )}

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
