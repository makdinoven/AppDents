import s from "./Button.module.scss";
import { Link } from "react-router-dom";
import { Trans } from "react-i18next";
import LoaderOverlay from "../LoaderOverlay/LoaderOverlay.tsx";

interface ButtonProps {
  loading?: boolean;
  text: string;
  link?: string;
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  type?: "button" | "submit" | "reset";
  variant?: "filled" | "outlined" | "outlined-dark";
}

const Button = ({
  loading,
  onClick,
  text,
  link,
  variant = "outlined",
  type = "button",
}: ButtonProps) => {
  return link ? (
    <Link className={s.btn} to={link}>
      <Trans i18nKey={text} />
    </Link>
  ) : (
    <button
      onClick={onClick}
      className={`${s.btn} ${variant ? s[variant] : ""} ${loading ? s.loading : ""}`}
      type={type}
    >
      <Trans i18nKey={text} />
      {loading && <LoaderOverlay />}
    </button>
  );
};

export default Button;
