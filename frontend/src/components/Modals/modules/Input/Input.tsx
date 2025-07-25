import React, { ReactNode, useState } from "react";
import s from "./Input.module.scss";
import { Trans } from "react-i18next";
import { EyeClosed, EyeOpened, ErrorIcon } from "../../../../assets/icons";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  state?: {
    state: "idle" | "success" | "validating" | "suggestion" | "warning";
    currentIndicator: ReactNode | null;
    suggestedEmail: string;
  };
  onSuggestionTooltipClick?: (value: string, e: React.MouseEvent) => void;
}

const Input: React.FC<InputProps> = ({
  error,
  type,
  state = {
    state: "idle",
    currentIndicator: null,
    suggestedEmail: "",
  },
  onSuggestionTooltipClick,
  ...props
}) => {
  const [visible, setVisible] = useState(false);
  const isPassword = type === "password";

  const inputType = isPassword ? (visible ? "text" : "password") : type;

  const isErrorVisible = error && !state.currentIndicator;
  const isIndicatorVisible = state.currentIndicator;
  const isTooltipVisible =
    state.state === "suggestion" || state.state === "warning";

  return (
    <div
      style={{ paddingRight: `${isPassword && error ? "65px" : ""}` }}
      className={`${s.input_wrapper} ${error && !state.currentIndicator ? s.error : ""}`}
    >
      <input {...props} type={inputType} />

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

      <div
        className={`${s.icon_wrapper}${isErrorVisible ? ` ${s.visible}` : ""}`}
      >
        {isErrorVisible && <ErrorIcon />}
        <div
          className={`${s.tooltip} ${s.error_tooltip}${isErrorVisible ? ` ${s.visible}` : ""}`}
        >
          <Trans i18nKey={error && error} />
        </div>
      </div>

      <div
        className={`${s.icon_wrapper}${isIndicatorVisible ? ` ${s.visible}` : ""}`}
      >
        {state.currentIndicator && state.currentIndicator}

        <button
          className={`${s.tooltip} ${s.state_tooltip} ${s.suggestion}${isTooltipVisible && state.state === "suggestion" ? ` ${s.visible}` : ""}`}
          onClick={(e) => {
            onSuggestionTooltipClick?.(state.suggestedEmail, e);
          }}
        >
          <Trans
            i18nKey={"suggestionTooltip"}
            values={{ suggestedEmail: state.suggestedEmail }}
          />
        </button>
        <div
          className={`${s.tooltip} ${s.state_tooltip}${isTooltipVisible && state.state === "warning" ? ` ${s.visible}` : ""}`}
        >
          <Trans i18nKey={"warningTooltip"} />
        </div>
      </div>
    </div>
  );
};

export default Input;
