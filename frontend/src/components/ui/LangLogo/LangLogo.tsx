import s from "./LangLogo.module.scss";
import {
  ArFlag,
  EnFlag,
  EsFlag,
  ItFlag,
  PtFlag,
  RuFlag,
} from "../../../assets/icons";
import { LANGUAGES } from "../../../common/helpers/commonConstants.ts";

export type LanguagesType = "EN" | "RU" | "ES" | "PT" | "AR" | "IT";

const LangLogo = ({
  lang,
  className,
  isChecked = false,
  isHoverable = false,
  onClick,
  hasPopUp,
}: {
  lang: LanguagesType;
  isChecked?: boolean;
  isHoverable?: boolean;
  hasPopUp?: boolean;
  className?: string;
  onClick?: () => void;
}) => {
  const flags = {
    EN: <EnFlag />,
    ES: <EsFlag />,
    RU: <RuFlag />,
    PT: <PtFlag />,
    AR: <ArFlag />,
    IT: <ItFlag />,
  };
  const label = LANGUAGES.find((item) => item.value === lang)?.label ?? null;

  return (
    <span
      onClick={onClick}
      className={`${s.logo} ${className ? className : ""} ${isChecked ? s.checked : ""} ${isHoverable ? s.hoverable : ""}`}
    >
      {flags[lang]}

      {hasPopUp && <div className={s.popup}>{label}</div>}
    </span>
  );
};

export default LangLogo;
