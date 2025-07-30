import s from "./InputTooltip.module.scss";
import { Trans } from "react-i18next";
import { useEffect, useState } from "react";

interface TooltipProps {
  type: "idle" | "error" | "suggestion" | "warning" | "success" | "validating";
  visible: boolean;
  textKey: string | null | undefined;
  suggestedEmail?: string;
  onTooltipClick?: (email: string) => void;
  tooltipCondition?: boolean;
  icon?: React.ReactNode;
}

const FADE_OUT_DELAY = 150;

const InputTooltip: React.FC<TooltipProps> = ({
  type,
  visible,
  textKey,
  suggestedEmail,
  onTooltipClick,
  tooltipCondition = false,
  icon,
}) => {
  const [cachedMsg, setCachedMsg] = useState<
    { key: string; value: string | null | undefined } | null | undefined
  >({
    key: textKey ? textKey : "",
    value: suggestedEmail ? suggestedEmail : "",
  });
  const iconClass = `${s.icon_wrapper} ${visible ? s.visible : ""}`;
  const tooltipClass = `${s.tooltip} ${s[`${type}_tooltip`]} ${tooltipCondition ? s.visible : ""}`;

  useEffect(() => {
    if (textKey) {
      setCachedMsg(textKey ? { key: textKey, value: suggestedEmail } : null);
    } else {
      const timeout = setTimeout(() => {
        setCachedMsg(null);
      }, FADE_OUT_DELAY);
      return () => clearTimeout(timeout);
    }
  }, [textKey]);

  return (
    <>
      <div className={iconClass}>{!!icon && icon}</div>
      <div
        lang={"en"}
        onClick={() => onTooltipClick?.(suggestedEmail || "")}
        className={tooltipClass}
      >
        <Trans
          i18nKey={cachedMsg?.key}
          values={{ suggestedEmail: cachedMsg?.value }}
        />
      </div>
    </>
  );
};

export default InputTooltip;
