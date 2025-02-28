import s from "./ArrowButton.module.scss";
import UnstyledButton from "../../CommonComponents/UnstyledButton.tsx";
import { Link } from "react-router-dom";
import CircleArrowSmall from "../../../common/Icons/CircleArrowSmall.tsx";

const ArrowButton = ({
  text,
  link,
  onClick,
  hasArrow = true,
}: {
  text: string;
  link?: string;
  hasArrow?: boolean;
  onClick?: any;
}) => {
  return link ? (
    <Link className={s.btn} to={link}>
      {text}
      {hasArrow && <CircleArrowSmall />}
    </Link>
  ) : (
    <UnstyledButton onClick={onClick} className={s.btn}>
      {text}
      {hasArrow && <CircleArrowSmall />}
    </UnstyledButton>
  );
};

export default ArrowButton;
