import s from "./MobileMenu.module.scss";
import {
  LS_TOKEN_KEY,
  NAV_BUTTONS,
} from "../../../common/helpers/commonConstants.ts";
import NavButton from "../../Header/modules/NavButton/NavButton.tsx";
import { ProfileIcon } from "../../../assets/icons";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../store/store.ts";
import { useLocation, useNavigate } from "react-router-dom";

import { isPromotionLanding } from "../../../common/helpers/helpers.ts";
import { useScreenWidth } from "../../../common/hooks/useScreenWidth.ts";
import { PATHS } from "../../../../app/routes/routes.ts";

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
      link: PATHS.PROFILE,
    });
  } else if (!isLogged && !accessToken) {
    buttons.push({
      icon: ProfileIcon,
      text: "login",
      onClick: () =>
        navigate(PATHS.LOGIN, {
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
      <div className={s.menu_content}>
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
                    navigate(PATHS.CART, {
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
                  btn.link === PATHS.MAIN
                    ? location.pathname === PATHS.MAIN
                    : location.pathname.includes(btn.link)
                }
              />
            </div>
          );
        })}
      </div>
    </nav>
  );
};

export default MobileMenu;
