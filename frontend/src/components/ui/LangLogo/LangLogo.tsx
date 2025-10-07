import s from "./LangLogo.module.scss";
// import { LANGUAGE_FLAGS } from "../../../common/helpers/commonConstants.ts";

export type LanguagesType = "EN" | "RU" | "ES" | "PT" | "AR" | "IT";

const LangLogo = ({
  lang,
  className,
  isChecked = false,
  isHoverable = false,
  onClick,
  // hasPopUp = false,
}: {
  lang: LanguagesType;
  isChecked?: boolean;
  isHoverable?: boolean;
  hasPopUp?: boolean;
  className?: string;
  onClick?: () => void;
}) => {
  // const label = LANGUAGES.find((item) => item.value === lang)?.label ?? null;
  // const Flag = LANGUAGE_FLAGS[lang];

  return (
    <span
      onClick={onClick}
      className={`${s.logo} ${className ? className : ""} ${isChecked ? s.checked : ""} ${isHoverable ? s.hoverable : ""}`}
    >
      {lang}

      {/*{hasPopUp && <div className={s.popup}>{label}</div>}*/}
    </span>
  );
};

export default LangLogo;
