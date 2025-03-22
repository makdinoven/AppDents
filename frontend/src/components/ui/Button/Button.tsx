import s from "./Button.module.scss";
import { Link } from "react-router-dom";

interface ButtonProps {
  // loading?: boolean;
  text: string;
  link?: string;
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  type?: "button" | "submit" | "reset";
}

const Button = ({
  // loading,
  onClick,
  text,
  link,
  type = "button",
}: ButtonProps) => {
  return link ? (
    <Link className={s.btn} to={link}>
      {/*{loading ? <Loader variant={"twoDots"} /> : text}*/}
      {text}
    </Link>
  ) : (
    <button onClick={onClick} className={s.btn} type={type}>
      {text}
      {/*{loading ? <Loader variant={"twoDots"} /> : text}*/}
    </button>
  );
};

export default Button;
