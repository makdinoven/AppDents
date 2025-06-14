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
import { AppDispatchType, AppRootStateType } from "../../store/store.ts";
import { useDispatch, useSelector } from "react-redux";
import { Path } from "../../routes/routes.ts";
import LanguageChanger from "../ui/LanguageChanger/LanguageChanger.tsx";
import {
  BooksIcon,
  DentsLogo,
  ProfessorsIcon,
  QuestionMark,
  SearchIcon,
} from "../../assets/logos/index";
import { useTriggerRef } from "../../common/context/TriggerRefContext.tsx";
import NavButton from "./modules/NavButton/NavButton.tsx";
import {
  AUTH_MODAL_ROUTES,
  LS_TOKEN_KEY,
  NAV_BUTTONS,
  OPEN_SEARCH_KEY,
} from "../../common/helpers/commonConstants.ts";
import UserIcon from "../../assets/Icons/UserIcon.tsx";
import { useScreenWidth } from "../../common/hooks/useScreenWidth.ts";
import { useScroll } from "../../common/hooks/useScroll.ts";
import {
  isPromotionLanding,
  scrollToElementById,
} from "../../common/helpers/helpers.ts";
import BurgerMenu from "../ui/BurgerMenu/BurgerMenu.tsx";
import { openModal } from "../../store/slices/landingSlice.ts";
import TimerBanner from "../ui/TimerBanner/TimerBanner.tsx";

const Header = () => {
  const dispatch = useDispatch<AppDispatchType>();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const { setTriggerRef } = useTriggerRef();
  const localTriggerRef = useRef<HTMLButtonElement | null>(null);
  const navigate = useNavigate();
  const isLogged = useSelector(
    (state: AppRootStateType) => state.user.isLogged,
  );
  const accessToken = localStorage.getItem(LS_TOKEN_KEY);
  const screenWidth = useScreenWidth();
  const isScrolled = useScroll();
  const isPromotion = isPromotionLanding(location.pathname);
  const oldPrice = useSelector(
    (state: AppRootStateType) => state.landing.oldPrice,
  );
  const newPrice = useSelector(
    (state: AppRootStateType) => state.landing.newPrice,
  );
  const quantity = useSelector(
    (state: AppRootStateType) => state.cart.quantity,
  );
  const [showStickyBanner, setShowStickyBanner] = useState(false);
  const [renderStickyBanner, setRenderStickyBanner] = useState(false);
  const discount = Number(
    (((oldPrice - newPrice) / oldPrice) * 100).toFixed(0),
  );
  const bannerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (localTriggerRef.current) {
      setTriggerRef(localTriggerRef);
    }
  }, [localTriggerRef, setTriggerRef]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) {
          setRenderStickyBanner(true);
          setShowStickyBanner(true);
        } else {
          setShowStickyBanner(false);
          setTimeout(() => setRenderStickyBanner(false), 300); // длительность анимации
        }
      },
      { threshold: 0 },
    );

    if (bannerRef.current) {
      observer.observe(bannerRef.current);
    }

    return () => {
      if (bannerRef.current) {
        observer.unobserve(bannerRef.current);
      }
    };
  }, []);

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
        <UnstyledButton
          onClick={() => navigate(Path.profile)}
          className={`${s.profile_button} ${location.pathname === Path.profile ? s.active : ""}`}
        >
          <UserIcon />
        </UnstyledButton>
      );
    }
  };

  const openSearch = () => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set(OPEN_SEARCH_KEY, "");
    setSearchParams(newParams, { replace: true });
  };

  const NAV_BUTTONS_PROMOTE = [
    {
      icon: BooksIcon,
      text: "nav.promote.program",
      targetId: "course-program",
    },
    {
      icon: ProfessorsIcon,
      text: "nav.promote.professors",
      targetId: "course-professors",
    },
    { icon: QuestionMark, text: "nav.promote.faq", targetId: "course-faq" },
  ].map((button) => ({
    ...button,
    onClick: () => scrollToElementById(button.targetId),
  }));

  return (
    <>
      {isPromotion && (
        <>
          <TimerBanner
            discount={discount}
            onClick={() => dispatch(openModal())}
            ref={bannerRef}
          />
          {renderStickyBanner && (
            <TimerBanner
              discount={discount}
              onClick={() => dispatch(openModal())}
              isSticky
              isHiding={!showStickyBanner}
            />
          )}
        </>
      )}
      <header className={`${s.header} ${isScrolled ? s.scrolled : ""}`}>
        <div className={s.content}>
          <nav className={s.nav}>
            <Link
              className={`${s.logo} ${isPromotion ? s.logoPromo : ""}`}
              to={Path.main}
            >
              <DentsLogo />
            </Link>
            {isPromotion ? (
              <>
                <div className={s.nav_center}>
                  {NAV_BUTTONS_PROMOTE.map((btn) => (
                    <NavButton
                      key={btn.text}
                      icon={btn.icon}
                      text={btn.text}
                      onClick={btn.onClick}
                    />
                  ))}
                </div>
                <BurgerMenu buttons={NAV_BUTTONS_PROMOTE} />
                {!!oldPrice && !!newPrice && (
                  <button
                    onClick={() => dispatch(openModal())}
                    className={s.buy_btn}
                  >
                    <Trans
                      i18nKey={"landing.buyFor"}
                      values={{
                        old_price: oldPrice,
                        new_price: newPrice,
                      }}
                      components={{
                        1: <span className="crossed-15" />,
                        2: <span className="highlight" />,
                      }}
                    />
                  </button>
                )}
              </>
            ) : (
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
            )}
          </nav>
        </div>
      </header>
    </>
  );
};

export default Header;
