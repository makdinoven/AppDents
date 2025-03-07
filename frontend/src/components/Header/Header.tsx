import s from "./Header.module.scss";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import LogoIcon from "../../common/Icons/LogoIcon.tsx";
import { Trans } from "react-i18next";
import UnstyledButton from "../CommonComponents/UnstyledButton.tsx";
import ModalWrapper from "../ModalWrapper/ModalWrapper.tsx";
import { useEffect, useRef, useState } from "react";
import LoginModal from "../Modals/LoginModal.tsx";
import SignUpModal from "../Modals/SignUpModal.tsx";
import ResetPasswordModal from "../Modals/ResetPasswordModal.tsx";
import { AppRootStateType } from "../../store/store.ts";
import { useSelector } from "react-redux";
import UserIcon from "../../common/Icons/UserIcon.tsx";
import { Path } from "../../routes/routes.ts";

const allowedModals = ["login", "sign-up", "password-reset"];

const Header = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
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

  return (
    <>
      <header className={s.header}>
        <div className={s.content}>
          <Link className={s.logo} to="/">
            <LogoIcon />
          </Link>
          {renderButton()}
        </div>
      </header>

      {triggerRef.current && isModalOpen && (
        <ModalWrapper
          cutoutPosition="top-right"
          cutoutOffsetY={15}
          triggerElement={triggerRef.current}
          isOpen={isModalOpen}
          onClose={handleCloseModal}
        >
          {modalType === "login" && <LoginModal onClose={handleCloseModal} />}
          {modalType === "sign-up" && <SignUpModal />}
          {modalType === "password-reset" && <ResetPasswordModal />}
        </ModalWrapper>
      )}
    </>
  );
};

export default Header;
