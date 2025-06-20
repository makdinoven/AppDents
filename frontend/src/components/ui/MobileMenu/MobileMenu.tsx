import s from "./MobileMenu.module.scss";
import {
  LS_TOKEN_KEY,
  NAV_BUTTONS,
} from "../../../common/helpers/commonConstants.ts";
import NavButton from "../../Header/modules/NavButton/NavButton.tsx";
import { ProfileIcon } from "../../../assets/logos/index";
import { Path } from "../../../routes/routes.ts";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../store/store.ts";
import { useLocation, useNavigate } from "react-router-dom";

import { isPromotionLanding } from "../../../common/helpers/helpers.ts";
import { useScreenWidth } from "../../../common/hooks/useScreenWidth.ts";

const MobileMenu = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const accessToken = localStorage.getItem(LS_TOKEN_KEY);
  const isLogged = useSelector(
    (state: AppRootStateType) => state.user.isLogged,
  );
  const quantity = useSelector(
    (state: AppRootStateType) => state.cart.quantity,
  );
  const screenWidth = useScreenWidth();

  const buttons: {
    icon: any;
    text: string;
    link?: any;
    onClick?: () => void;
  }[] = [...NAV_BUTTONS];

  if (isLogged && accessToken) {
    buttons.push({
      icon: ProfileIcon,
      text: "nav.profile",
      link: Path.profile,
    });
  } else if (!isLogged && !accessToken) {
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
  } else {
    buttons.push({
      icon: ProfileIcon,
      text: "...",
    });
  }

  if (isPromotionLanding(location.pathname) || screenWidth >= 769) {
    return null;
  }

  return (
    <nav className={s.menu}>
      {buttons.map((btn, i) => {
        if (btn.text.includes("cart")) {
          return (
            <div key={i} className={s.btn_wrapper}>
              <NavButton
                icon={btn.icon}
                text={btn.text}
                direction={"vertical"}
                quantity={quantity}
                onClick={() =>
                  navigate(Path.cart, {
                    state: { backgroundLocation: location },
                  })
                }
                isActive={location.pathname.includes(btn.link)}
              />
            </div>
          );
        }

        return (
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
        );
      })}
    </nav>
  );
};

export default MobileMenu;
