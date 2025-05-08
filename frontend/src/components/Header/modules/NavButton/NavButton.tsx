import s from "./NavButton.module.scss";
import { Link } from "react-router-dom";
import { Trans } from "react-i18next";

const NavButton = ({
  icon: Icon,
  text,
  link,
  onClick,
  appearance,
  isActive,
  direction = "horizontal",
}: {
  direction?: "horizontal" | "vertical";
  isActive?: boolean;
  appearance?: "light";
  icon: React.ElementType;
  text?: string;
  link?: string;
  onClick?: () => void;
}) => {
  if (link) {
    return (
      <Link
        onClick={onClick}
        className={`${s.navButton} ${appearance ? s.light : ""} ${isActive ? s.active : ""} ${direction === "vertical" ? s.vertical : ""}`}
        to={link}
      >
        <Icon className={s.icon} />
        {text && <Trans i18nKey={text} />}
      </Link>
    );
  } else {
    return (
      <button
        onClick={onClick}
        className={`${s.navButton} ${appearance ? s.light : ""} ${isActive ? s.active : ""} ${direction === "vertical" ? s.vertical : ""}`}
      >
        <Icon className={s.icon} />
        {text && <Trans i18nKey={text} />}
      </button>
    );
  }
};

export default NavButton;
