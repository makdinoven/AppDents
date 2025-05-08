import s from "./Header.module.scss";
import {
  Link,
  useLocation,
  useNavigate,
  useSearchParams,
} from "react-router-dom";
import { Trans } from "react-i18next";
import UnstyledButton from "../CommonComponents/UnstyledButton.tsx";
import { useEffect, useRef, useState } from "react";
import { AppRootStateType } from "../../store/store.ts";
import { useSelector } from "react-redux";
import { Path } from "../../routes/routes.ts";
import LanguageChanger from "../ui/LanguageChanger/LanguageChanger.tsx";
import { DentsLogo, SearchIcon } from "../../assets/logos/index";
import { useTriggerRef } from "../../common/context/TriggerRefContext.tsx";
import NavButton from "./modules/NavButton/NavButton.tsx";
import {
  AUTH_MODAL_ROUTES,
  NAV_BUTTONS,
} from "../../common/helpers/commonConstants.ts";
import UserIcon from "../../assets/Icons/UserIcon.tsx";
import SearchModal from "../ui/SearchModal/SearchModal.tsx";

const OPEN_SEARCH_KEY = "GS";

const Header = () => {
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const { setTriggerRef } = useTriggerRef();
  const localTriggerRef = useRef<HTMLButtonElement | null>(null);
  const navigate = useNavigate();
  const isLogged = useSelector(
    (state: AppRootStateType) => state.user.isLogged,
  );
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 0);
    };

    window.addEventListener("scroll", handleScroll);
    return () => {
      window.removeEventListener("scroll", handleScroll);
    };
  }, []);

  useEffect(() => {
    if (localTriggerRef.current) {
      setTriggerRef(localTriggerRef);
    }
  }, [localTriggerRef, setTriggerRef]);

  const renderLoginButton = () => {
    if (!isLogged) {
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
          className={`${s.login_btn} ${AUTH_MODAL_ROUTES.includes(location.pathname) && s.active}`}
        >
          <Trans i18nKey="login" />
        </UnstyledButton>
      );
    }
    return (
      <UnstyledButton
        onClick={() => navigate(Path.profile)}
        className={`${s.login_btn} ${s.profile_button} ${location.pathname === Path.profile && s.active}`}
      >
        <UserIcon />
      </UnstyledButton>
    );
  };

  const openSearch = () => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set(OPEN_SEARCH_KEY, "");
    setSearchParams(newParams, { replace: true });
  };

  const renderNavButtons = () => {
    return NAV_BUTTONS.map((btn) => (
      <NavButton
        key={btn.text}
        icon={btn.icon}
        text={btn.text}
        link={btn.link}
        isActive={location.pathname === btn.link}
      />
    ));
  };

  return (
    <>
      <header className={`${s.header} ${isScrolled ? s.scrolled : ""}`}>
        <div className={s.content}>
          <nav className={s.nav}>
            <Link className={s.logo} to={Path.main}>
              <DentsLogo />
            </Link>
            <div className={s.nav_center}>{renderNavButtons()}</div>

            <div className={s.nav_side}>
              <NavButton
                onClick={openSearch}
                icon={SearchIcon}
                text={"nav.search"}
                isActive={location.pathname === Path.search}
              />
              <LanguageChanger />
              {renderLoginButton()}
            </div>
          </nav>
        </div>
      </header>

      <SearchModal openKey={OPEN_SEARCH_KEY} />
    </>
  );
};

export default Header;
