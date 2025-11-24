import { useLocation, useNavigate } from "react-router-dom";
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
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <span
      className={`${s.link} ${variant === "uppercase" ? s.uppercase : ""}`}
      onClick={() =>
        navigate(link, {
          state: {
            backgroundLocation: location.state?.backgroundLocation || {
              pathname: location.pathname,
              search: location.search,
            },
          },
          replace: true,
        })
      }
    >
      <Trans i18nKey={text} />
    </span>
  );
};

export default ModalLink;
