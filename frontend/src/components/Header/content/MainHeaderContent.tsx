import s from "../Header.module.scss";
import {
  AUTH_MODAL_ROUTES,
  LS_TOKEN_KEY,
  NAV_BUTTONS,
  OPEN_SEARCH_KEY,
} from "../../../common/helpers/commonConstants.ts";
import NavButton from "../modules/NavButton/NavButton.tsx";
import { Path } from "../../../routes/routes.ts";
import { SearchIcon } from "../../../assets/icons/index.ts";
import LanguageChanger from "../../ui/LanguageChanger/LanguageChanger.tsx";
import UnstyledButton from "../../CommonComponents/UnstyledButton.tsx";
import { Trans } from "react-i18next";
import { UserFilled } from "../../../assets/icons";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../store/store.ts";
import {
  Link,
  useLocation,
  useNavigate,
  useSearchParams,
} from "react-router-dom";
import { useScreenWidth } from "../../../common/hooks/useScreenWidth.ts";
import { useEffect, useRef } from "react";
import { useTriggerRef } from "../../../common/context/TriggerRefContext.tsx";

const MainHeaderContent = () => {
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const isLogged = useSelector(
    (state: AppRootStateType) => state.user.isLogged
  );
  const accessToken = localStorage.getItem(LS_TOKEN_KEY);
  const screenWidth = useScreenWidth();
  const quantity = useSelector(
    (state: AppRootStateType) => state.cart.quantity
  );
  const { setTriggerRef } = useTriggerRef();
  const localTriggerRef = useRef<HTMLButtonElement | null>(null);

  const openSearch = () => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set(OPEN_SEARCH_KEY, "");
    setSearchParams(newParams, { replace: true });
  };

  useEffect(() => {
    if (localTriggerRef.current) {
      setTriggerRef(localTriggerRef);
    }
  }, [localTriggerRef, setTriggerRef]);

  const renderLoginButton = () => {
    if (screenWidth > 768) {
      if (!isLogged && !accessToken) {
        return (
          <UnstyledButton
            ref={localTriggerRef}
            onClick={() =>
              navigate(Path.login, {
                state: {
                  backgroundLocation: location,
                },
              })
            }
            className={`${s.login_btn} ${AUTH_MODAL_ROUTES.includes(location.pathname) ? s.active : ""}`}
          >
            <Trans i18nKey="login" />
          </UnstyledButton>
        );
      }
      return (
        <Link
          to={Path.profile}
          className={`${s.profile_button} ${location.pathname === Path.profile ? s.active : ""}`}
        >
          <UserFilled />
        </Link>
      );
    }
  };

  return (
    <>
      <div className={s.nav_center}>
        {NAV_BUTTONS.map((btn) => {
          if (btn.text.includes("cart")) {
            return (
              <NavButton
                key={btn.text}
                icon={btn.icon}
                text={btn.text}
                quantity={quantity}
                onClick={() =>
                  navigate(Path.cart, {
                    state: { backgroundLocation: location },
                  })
                }
                isActive={location.pathname === btn.link}
              />
            );
          }

          return (
            <NavButton
              key={btn.text}
              icon={btn.icon}
              text={btn.text}
              link={btn.link}
              isActive={location.pathname === btn.link}
            />
          );
        })}
      </div>
      <div className={s.nav_side}>
        <NavButton
          onClick={openSearch}
          icon={SearchIcon}
          // text={"nav.search"}
          isActive={location.pathname === Path.search}
        />
        <LanguageChanger />
        {renderLoginButton()}
      </div>
    </>
  );
};

export default MainHeaderContent;
