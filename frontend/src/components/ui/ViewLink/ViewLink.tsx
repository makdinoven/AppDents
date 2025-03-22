import s from "./ViewLink.module.scss";
import { Link } from "react-router-dom";
import { Trans } from "react-i18next";
import Arrow from "../../../common/Icons/Arrow.tsx";

const ViewLink = ({ link, text }: { link: string; text: string }) => {
  return (
    <Link className={s.link} to={link}>
      <Trans i18nKey={text} />
      <Arrow />
    </Link>
  );
};

export default ViewLink;
