import s from "./ArrowButton.module.scss";
import { Link } from "react-router-dom";
import { CircleArrowSmall } from "../../../assets/icons/index.ts";
import { Trans } from "react-i18next";

const ArrowButton = ({
  ref,
  text,
  link,
  onClick,
  children,
}: {
  ref?: any;
  text?: string;
  link?: string;
  onClick?: any;
  children?: any;
}) => {
  return link ? (
    <Link className={s.btn} to={link}>
      <Trans i18nKey={text} />
      {children && <span>{children}</span>}
      <CircleArrowSmall />
    </Link>
  ) : (
    <button ref={ref} onClick={onClick} className={s.btn}>
      <Trans i18nKey={text} />
      {children && <span>{children}</span>}
      <CircleArrowSmall />
    </button>
  );
};

export default ArrowButton;
