import { Link, useLocation } from "react-router-dom";
import { Trans } from "react-i18next";
import s from "./ModalLink.module.scss";

const ModalLink = ({
  link,
  text,
  variant,
}: {
  link: string;
  text: string;
  variant?: "uppercase";
}) => {
  const location = useLocation();

  const pathParts = location.pathname.split("/").filter(Boolean);
  pathParts.pop();

  const basePath = pathParts.join("/");

  return (
    <Link
      className={`${s.link} ${variant === "uppercase" ? s.uppercase : ""}`}
      to={`${basePath}${link}`}
    >
      <Trans i18nKey={text} />
    </Link>
  );
};

export default ModalLink;
