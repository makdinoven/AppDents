import s from "./LangLogo.module.scss";
import {
  ArFlag,
  EnFlag,
  EsFlag,
  ItFlag,
  PtFlag,
  RuFlag,
} from "../../../assets/icons";

export type LanguagesType = "EN" | "RU" | "ES" | "PT" | "AR" | "IT";

const LangLogo = ({
  lang,
  className,
  isChecked = false,
  isHoverable = false,
  onClick,
}: {
  lang: LanguagesType;
  isChecked?: boolean;
  isHoverable?: boolean;
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
  return (
    <span
      onClick={onClick}
      className={`${s.logo} ${className ? className : ""} ${isChecked ? s.checked : ""} ${isHoverable ? s.hoverable : ""}`}
    >
      {flags[lang]}
    </span>
  );
};

export default LangLogo;
