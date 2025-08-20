import s from "./PrettyButton.module.scss";
import UnstyledButton from "../../CommonComponents/UnstyledButton.tsx";
import { Trans } from "react-i18next";
import LoaderOverlay from "../LoaderOverlay/LoaderOverlay.tsx";

const PrettyButton = ({
  text,
  variant = "default",
  onClick,
  loading,
  className,
}: {
  text: string;
  loading?: boolean;
  variant?: "danger" | "primary" | "default" | "default_white_hover";
  onClick?: any;
  className?: string;
}) => {
  return (
    <UnstyledButton
      onClick={onClick}
      className={`${s.btn} ${className ? className : ""} ${s[variant] || ""} ${loading ? s.loading : ""}`}
    >
      {loading && <LoaderOverlay />}
      <Trans i18nKey={text} />
    </UnstyledButton>
  );
};

export default PrettyButton;
