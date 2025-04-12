import s from "./PrettyButton.module.scss";
import UnstyledButton from "../../CommonComponents/UnstyledButton.tsx";
import Loader from "../Loader/Loader.tsx";
import { Trans } from "react-i18next";

const PrettyButton = ({
  text,
  variant = "default",
  onClick,
  loading,
}: {
  text: string;
  loading?: boolean;
  variant?: "danger" | "primary" | "default";
  onClick?: any;
}) => {
  return (
    <UnstyledButton
      onClick={onClick}
      className={`${s.btn} ${s[variant] || ""}`}
    >
      {loading ? <Loader /> : <Trans i18nKey={text} />}
    </UnstyledButton>
  );
};

export default PrettyButton;
