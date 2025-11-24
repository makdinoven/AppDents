import s from "./ToggleButton.module.scss";
import { Trans } from "react-i18next";

interface TabButtonProps {
  text: string;
  isActive?: boolean;
  onClick?: () => void;
}

const ToggleButton = ({ onClick, text, isActive }: TabButtonProps) => {
  return (
    <button
      onClick={onClick}
      className={`${s.btn} ${isActive ? s.active : ""}`}
    >
      <Trans i18nKey={text} />
    </button>
  );
};
export default ToggleButton;
