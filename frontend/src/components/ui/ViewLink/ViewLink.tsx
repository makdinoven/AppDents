import s from "./ViewLink.module.scss";
import { Link } from "react-router-dom";
import { Trans } from "react-i18next";
import Arrow from "../../../assets/Icons/Arrow.tsx";

const ViewLink = ({
  isExternal,
  link,
  text,
  className,
}: {
  className?: string;
  isExternal?: boolean;
  link?: string;
  text: string;
}) => {
  return isExternal ? (
    <a
      className={`${s.link} ${className ? className : ""}`}
      href={link}
      target="_blank"
      rel="noopener noreferrer"
    >
      <Trans i18nKey={text} />
      <Arrow />
    </a>
  ) : link ? (
    <Link
      className={`${s.link} ${className ? className : ""}`}
      to={link ? link : ""}
    >
      <Trans i18nKey={text} />
      <Arrow />
    </Link>
  ) : (
    <span className={`${s.link} ${className ? className : ""}`}>
      <Trans i18nKey={text} />
      <Arrow />
    </span>
  );
};

export default ViewLink;
