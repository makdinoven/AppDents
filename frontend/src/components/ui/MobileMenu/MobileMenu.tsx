import s from "./MobileMenu.module.scss";
import { NAV_BUTTONS } from "../../../common/helpers/commonConstants.ts";
import NavButton from "../../Header/modules/NavButton/NavButton.tsx";
import { ProfileIcon } from "../../../assets/logos/index";
import { Path } from "../../../routes/routes.ts";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../store/store.ts";
import { useLocation, useNavigate } from "react-router-dom";
import { useMemo } from "react";

const MobileMenu = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const isLogged = useSelector(
    (state: AppRootStateType) => state.user.isLogged,
  );
  const isFromFacebook = useMemo(() => {
    const searchParams = new URLSearchParams(location.search);
    return searchParams.has("fbclid");
  }, [location.search]);

  const buttons: {
    icon: any;
    text: string;
    link?: any;
    onClick?: () => void;
  }[] = [...NAV_BUTTONS];

  if (isLogged) {
    buttons.push({
      icon: ProfileIcon,
      text: "nav.profile",
      link: Path.profile,
    });
  } else {
    buttons.push({
      icon: ProfileIcon,
      text: "login",
      onClick: () =>
        navigate(Path.login, {
          state: {
            backgroundLocation: location,
          },
        }),
    });
  }

  if (isFromFacebook) {
    return null;
  }

  if (location.pathname.includes(Path.landing)) {
    return null;
  }

  return (
    <nav className={s.menu}>
      {buttons.map((btn) => (
        <div key={btn.text} className={s.btn_wrapper}>
          <NavButton
            icon={btn.icon}
            text={btn.text}
            link={btn.link}
            direction={"vertical"}
            onClick={btn.onClick}
            isActive={
              btn.link === Path.main
                ? location.pathname === Path.main
                : location.pathname.includes(btn.link)
            }
          />
        </div>
      ))}
    </nav>
  );
};

export default MobileMenu;
