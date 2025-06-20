import { useLocation, useNavigate } from "react-router-dom";
import ModalWrapper from "../Modals/ModalWrapper/ModalWrapper";
import { Path } from "../../routes/routes";
import { useEffect, useMemo } from "react";
import LoginModal from "../Modals/LoginModal.tsx";
import { useTriggerRef } from "../../common/context/TriggerRefContext.tsx";
import SignUpModal from "../Modals/SignUpModal.tsx";
import ForgotPasswordModal from "../Modals/ForgotPasswordModal.tsx";
import { AUTH_MODAL_ROUTES } from "../../common/helpers/commonConstants.ts";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../store/store.ts";

const AuthModalManager = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const isLogged = useSelector(
    (state: AppRootStateType) => state.user.isLogged,
  );
  const { triggerRef } = useTriggerRef();
  const isModalOpen = AUTH_MODAL_ROUTES.includes(location.pathname);

  const handleClose = () => {
    const backgroundLocation = location.state?.backgroundLocation;
    if (backgroundLocation) {
      navigate(backgroundLocation.pathname + backgroundLocation.search, {
        replace: true,
      });
    } else {
      navigate(Path.main, { replace: true });
    }
  };

  const modalContent = useMemo(() => {
    switch (location.pathname) {
      case Path.login:
        return {
          title: "login",
          component: <LoginModal />,
        };
      case Path.signUp:
        return {
          title: "signup",
          component: <SignUpModal />,
        };
      case Path.passwordReset:
        return {
          title: "passwordReset",
          component: <ForgotPasswordModal />,
        };
      default:
        return null;
    }
  }, [location.pathname]);

  useEffect(() => {
    if (isLogged && isModalOpen) {
      navigate(Path.profile, { replace: true });
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }, [isLogged, isModalOpen, navigate]);

  if (!isModalOpen || !modalContent) return null;

  return (
    <ModalWrapper
      title={modalContent.title}
      cutoutPosition={`${triggerRef ? "top-right" : "none"}`}
      cutoutOffsetY={15}
      triggerElement={triggerRef?.current}
      isOpen={isModalOpen}
      onClose={handleClose}
    >
      {modalContent.component}
    </ModalWrapper>
  );
};

export default AuthModalManager;
