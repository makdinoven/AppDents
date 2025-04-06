import s from "./ViewLink.module.scss";
import { Link } from "react-router-dom";
import { Trans } from "react-i18next";
import Arrow from "../../../common/Icons/Arrow.tsx";

const ViewLink = ({
  isExternal,
  link,
  text,
}: {
  isExternal?: boolean;
  link?: string;
  text: string;
}) => {
  return isExternal ? (
    <a className={s.link} href={link} target="_blank" rel="noopener noreferrer">
      <Trans i18nKey={text} />
      <Arrow />
    </a>
  ) : link ? (
    <Link className={s.link} to={link ? link : ""}>
      <Trans i18nKey={text} />
      <Arrow />
    </Link>
  ) : (
    <span className={s.link}>
      <Trans i18nKey={text} />
      <Arrow />
    </span>
  );
};

export default ViewLink;
