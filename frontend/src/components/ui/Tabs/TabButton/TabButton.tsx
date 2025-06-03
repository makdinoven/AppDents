import s from "./TabButton.module.scss";
import { Trans } from "react-i18next";

const TabButton = ({
  isActive,
  onClick,
  text,
}: {
  text: string;
  isActive: boolean;
  onClick: () => void;
}) => {
  return (
    <button
      onClick={onClick}
      className={`${s.btn} ${isActive ? s.active : ""}`}
    >
      <Trans i18nKey={text} />
    </button>
  );
};

export default TabButton;
