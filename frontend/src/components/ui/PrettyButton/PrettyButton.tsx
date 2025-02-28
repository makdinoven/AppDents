import s from "./PrettyButton.module.scss";
import UnstyledButton from "../../CommonComponents/UnstyledButton.tsx";
import Loader from "../Loader/Loader.tsx";

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
      {loading ? <Loader /> : text}
    </UnstyledButton>
  );
};

export default PrettyButton;
