import s from "./ExtendedToggleButton.module.scss";
import { Trans } from "react-i18next";
import { ArrowX } from "../../../assets/icons";
import LoaderOverlay from "../LoaderOverlay/LoaderOverlay.tsx";

type ButtonProps = {
  handleClick: () => void;
  isActive: boolean;
  isLastActive?: boolean;
  isDisabled?: boolean;
  transKey: string;
  num?: number;
  loading?: boolean;
  isClickable?: boolean;
};

const ExtendedToggleButton = ({
  handleClick,
  isActive,
  isClickable,
  isDisabled,
  isLastActive,
  transKey,
  num = 0,
  loading,
}: ButtonProps) => {
  return (
    <button
      onClick={handleClick}
      className={`${s.toggle_btn} ${loading ? s.loading : ""} ${isClickable ? "" : s.no_click} ${isActive ? s.active : ""} ${isLastActive ? s.last_active : ""} ${isDisabled ? s.disabled : ""}`}
    >
      <Trans i18nKey={transKey} />
      <span className={s.num}>
        {loading && !isDisabled && <LoaderOverlay />}
        <span className={`${loading ? s.hidden : ""}`}>{num}</span>
      </span>
      <span className={s.line}></span>
      <ArrowX className={`${s.arrow_icon} ${isActive ? "" : s.hidden}`} />
    </button>
  );
};

export default ExtendedToggleButton;
