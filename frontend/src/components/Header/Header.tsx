import s from "./Header.module.scss";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { Trans } from "react-i18next";
import UnstyledButton from "../CommonComponents/UnstyledButton.tsx";
import ModalWrapper from "../Modals/ModalWrapper/ModalWrapper.tsx";
import { useEffect, useRef, useState } from "react";
import LoginModal from "../Modals/LoginModal.tsx";
import SignUpModal from "../Modals/SignUpModal.tsx";
import ForgotPasswordModal from "../Modals/ForgotPasswordModal.tsx";
import { AppRootStateType } from "../../store/store.ts";
import { useSelector } from "react-redux";
import UserIcon from "../../assets/Icons/UserIcon.tsx";
import { Path } from "../../routes/routes.ts";
import LanguageChanger from "../ui/LanguageChanger/LanguageChanger.tsx";
import { DentsLogo, SearchIcon } from "../../assets/logos/index";
import SearchDropdown from "../CommonComponents/SearchDropdown/SearchDropdown.tsx";

const allowedModals = ["login", "sign-up", "password-reset"];

const Header = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const navigate = useNavigate();
  const location = useLocation();
  const { modalType } = useParams();
  const userEmail = useSelector((state: AppRootStateType) => state.user.email);

  useEffect(() => {
    if (modalType && allowedModals.includes(modalType)) {
      setIsModalOpen(true);
    } else {
      const pathWithoutModal = location.pathname
        .split("/")
        .filter((segment) => !allowedModals.includes(segment))
        .join("/");

      navigate(pathWithoutModal || "/", { replace: true });
      setIsModalOpen(false);
    }
  }, [modalType, navigate]);

  const handleOpenModal = (modal: string) => {
    const newPath = location.pathname.endsWith("/")
      ? `${location.pathname}${modal}`
      : `${location.pathname}/${modal}`;

    navigate(newPath, { replace: true });
  };

  const handleCloseModal = () => {
    const pathWithoutModal = location.pathname
      .split("/")
      .filter((segment) => !allowedModals.includes(segment))
      .join("/");

    navigate(pathWithoutModal || "/", { replace: true });
  };

  const renderButton = () => {
    if (!userEmail) {
      return (
        <UnstyledButton
          ref={triggerRef}
          onClick={() => handleOpenModal("login")}
          className={`${s.login_btn} ${modalType ? s.login_btn_active : ""}`}
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

  const modalContent = modalType
    ? {
        login: {
          title: "login",
          component: <LoginModal onClose={handleCloseModal} />,
        },
        "sign-up": { title: "signup", component: <SignUpModal /> },
        "password-reset": {
          title: "passwordReset",
          component: <ForgotPasswordModal />,
        },
      }[modalType]
    : undefined;

  return (
    <>
      <div className={s.working_warn}>
        <h2>We'll Be Back Soon</h2>
        <p>
          We're currently performing some updates to improve your learning
          experience.
        </p>
        <p>
          Our course platform is temporarily unavailable due to scheduled
          maintenance.
        </p>
        <p>
          Please check back shortly — new and improved features are on the way!
        </p>
        <p>
          Thank you for your patience and continued interest in our courses.
        </p>
        <p>— The Dent-S Team</p>
      </div>
      <header className={s.header}>
        <div className={s.content}>
          <Link className={s.logo} to={Path.main}>
            <DentsLogo />
          </Link>
          <nav className={s.nav}>
            {![Path.main, Path.login, Path.passwordReset, Path.signUp].includes(
              location.pathname,
            ) && (
              <UnstyledButton className={s.login_btn}>
                <Link to={Path.main}>
                  <Trans i18nKey="home" />
                </Link>
              </UnstyledButton>
            )}
            <UnstyledButton
              className={s.search_button}
              onClick={() => setShowSearch(true)}
            >
              <SearchIcon />
            </UnstyledButton>
            <LanguageChanger />
            {renderButton()}
          </nav>
        </div>
      </header>

      {showSearch && (
        <SearchDropdown
          showDropdown={showSearch}
          setShowDropdown={setShowSearch}
        />
      )}

      {triggerRef.current && isModalOpen && modalContent && (
        <ModalWrapper
          title={modalContent.title}
          cutoutPosition="top-right"
          cutoutOffsetY={15}
          triggerElement={triggerRef.current}
          isOpen={isModalOpen}
          onClose={handleCloseModal}
        >
          {modalContent.component}
        </ModalWrapper>
      )}
    </>
  );
};

export default Header;
