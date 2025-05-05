import s from "./Header.module.scss";
import {
  Link,
  useLocation,
  useNavigate,
  useSearchParams,
} from "react-router-dom";
import { Trans } from "react-i18next";
import UnstyledButton from "../CommonComponents/UnstyledButton.tsx";
import { useEffect, useRef } from "react";
import { AppRootStateType } from "../../store/store.ts";
import { useSelector } from "react-redux";
import UserIcon from "../../assets/Icons/UserIcon.tsx";
import { Path } from "../../routes/routes.ts";
import LanguageChanger from "../ui/LanguageChanger/LanguageChanger.tsx";
import { DentsLogo, HomeIcon, SearchIcon } from "../../assets/logos/index";
import SearchDropdown from "../CommonComponents/SearchDropdown/SearchDropdown.tsx";
import Glasses from "../../assets/Icons/Glasses.tsx";
import { useTriggerRef } from "../../common/context/TriggerRefContext.tsx";

const OPEN_SEARCH_KEY = "GS";

const Header = () => {
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const { setTriggerRef } = useTriggerRef();
  const localTriggerRef = useRef<HTMLButtonElement | null>(null);
  const navigate = useNavigate();
  const userEmail = useSelector((state: AppRootStateType) => state.user.email);

  useEffect(() => {
    if (localTriggerRef.current) {
      setTriggerRef(localTriggerRef);
    }
  }, [localTriggerRef, setTriggerRef]);

  const renderButton = () => {
    if (!userEmail) {
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
          className={s.login_btn}
        >
          <Trans i18nKey="login" />
        </UnstyledButton>
      );
    }
    return (
      <UnstyledButton
        onClick={() => navigate(Path.profile)}
        className={s.login_btn}
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

  return (
    <>
      <header className={s.header}>
        <div className={s.content}>
          <Link className={s.logo} to={Path.main}>
            <DentsLogo />
          </Link>
          <nav className={s.nav}>
            <div className={s.nav_buttons}>
              <UnstyledButton className={s.home_button}>
                <Link to={Path.main}>
                  <HomeIcon />
                </Link>
              </UnstyledButton>
              <UnstyledButton className={s.professors_button}>
                <Link to={Path.professors}>
                  <Glasses />
                </Link>
              </UnstyledButton>
              <UnstyledButton className={s.search_button} onClick={openSearch}>
                <SearchIcon />
              </UnstyledButton>
              <LanguageChanger />
            </div>

            {renderButton()}
          </nav>
        </div>
      </header>

      <SearchDropdown openKey={OPEN_SEARCH_KEY} />
    </>
  );
};

export default Header;
