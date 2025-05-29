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
  quantity,
  direction = "horizontal",
}: {
  direction?: "horizontal" | "vertical";
  isActive?: boolean;
  appearance?: "light" | "footer";
  icon?: React.ElementType;
  text?: string;
  link?: string;
  onClick?: () => void;
  quantity?: number;
}) => {
  if (link) {
    return (
      <Link
        onClick={onClick}
        className={`${s.navButton}
         ${appearance === "light" ? s.light : ""}
          ${appearance === "footer" ? s.footer : ""}
           ${isActive ? s.active : ""}
            ${direction === "vertical" ? s.vertical : ""}`}
        to={link}
      >
        {Icon && (
          <span className={s.icon_wrapper}>
            <Icon className={s.icon} />
            {!!quantity && (
              <span className={s.quantity_circle}>{quantity}</span>
            )}
          </span>
        )}
        {text && <Trans i18nKey={text} />}
      </Link>
    );
  } else {
    return (
      <button
        onClick={onClick}
        className={`${s.navButton}
         ${appearance === "light" ? s.light : ""}
          ${appearance === "footer" ? s.footer : ""}
           ${isActive ? s.active : ""}
            ${direction === "vertical" ? s.vertical : ""}`}
      >
        {Icon && (
          <span className={s.icon_wrapper}>
            <Icon className={s.icon} />
            {!!quantity && (
              <span className={s.quantity_circle}>{quantity}</span>
            )}
          </span>
        )}
        {text && <Trans i18nKey={text} />}
      </button>
    );
  }
};

export default NavButton;
