import s from "./Button.module.scss";
import { Link } from "react-router-dom";

interface ButtonProps {
  text: string;
  link?: string;
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  type?: "button" | "submit" | "reset";
  className?: string;
}

const Button = ({
  onClick,
  text,
  link,
  type = "button",
  className,
}: ButtonProps) => {
  return link ? (
    <Link className={`${s.btn} ${className || ""}`} to={link}>
      {text}
    </Link>
  ) : (
    <button
      onClick={onClick}
      className={`${s.btn} ${className || ""}`}
      type={type}
    >
      {text}
    </button>
  );
};

export default Button;
