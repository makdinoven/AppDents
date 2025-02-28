import { Link, useLocation } from "react-router-dom";
import { Trans } from "react-i18next";

const ModalLink = ({ link, text }: { link: string; text: string }) => {
  const location = useLocation();

  const pathParts = location.pathname.split("/").filter(Boolean);
  pathParts.pop();

  const basePath = pathParts.join("/");

  return (
    <Link to={`${basePath}${link}`}>
      <Trans i18nKey={text} />
    </Link>
  );
};

export default ModalLink;
