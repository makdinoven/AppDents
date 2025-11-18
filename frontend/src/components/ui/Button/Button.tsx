import s from "./Button.module.scss";
import { Link } from "react-router-dom";
import LoaderOverlay from "../LoaderOverlay/LoaderOverlay.tsx";
import { Trans } from "react-i18next";

interface ButtonProps {
  disabled?: any;
  loading?: boolean;
  link?: string;
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  type?: "button" | "submit" | "reset";
  variant?:
    | "filled"
    | "filled_light"
    | "filled_dark"
    | "outlined"
    | "outlined_dark"
    | "disabled";
  children?: React.ReactNode;
  text?: string;
  icon?: React.ReactNode | null;
  className?: string;
}

const Button = ({
  disabled,
  loading,
  link,
  onClick,
  type = "button",
  variant = "outlined",
  children,
  text,
  icon,
  className,
}: ButtonProps) => {
  return link ? (
    <Link className={s.btn} to={link}></Link>
  ) : (
    <button
      disabled={disabled}
      onClick={onClick}
      className={`${s.btn} ${variant ? s[variant] : ""} ${className ? className : ""} ${loading ? s.loading : ""}`}
      type={type}
    >
      {children && <span>{children}</span>}
      {text && (
        <span>
          <Trans i18nKey={text} />
        </span>
      )}
      {icon && icon}
      {loading && <LoaderOverlay />}
    </button>
  );
};

export default Button;
