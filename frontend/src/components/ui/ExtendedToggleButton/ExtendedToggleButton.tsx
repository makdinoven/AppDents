import s from "./ExtendedToggleButton.module.scss";
import { Trans } from "react-i18next";
import { ArrowX } from "../../../assets/icons";

type ButtonProps = {
  handleClick: () => void;
  isActive: boolean;
  isLastActive?: boolean;
  isDisabled?: boolean;
  transKey: string;
  num?: number;
};

const ExtendedToggleButton = ({
  handleClick,
  isActive,
  isDisabled,
  isLastActive,
  transKey,
  num,
}: ButtonProps) => {
  return (
    <button
      onClick={handleClick}
      className={`${s.toggle_btn} ${isActive ? s.active : ""} ${isLastActive ? s.last_active : ""} ${isDisabled ? s.disabled : ""}`}
    >
      <Trans i18nKey={transKey} />
      <span key={num} className={s.num}>
        {num}
      </span>
      <span className={s.line}></span>
      <ArrowX className={`${s.arrow_icon} ${isActive ? "" : s.hidden}`} />
    </button>
  );
};

export default ExtendedToggleButton;
