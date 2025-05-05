import { useLocation, useNavigate } from "react-router-dom";
import ModalWrapper from "../Modals/ModalWrapper/ModalWrapper";
import { Path } from "../../routes/routes";
import { useMemo } from "react";
import LoginModal from "../Modals/LoginModal.tsx";
import { useTriggerRef } from "../../common/context/TriggerRefContext.tsx";
import SignUpModal from "../Modals/SignUpModal.tsx";
import ForgotPasswordModal from "../Modals/ForgotPasswordModal.tsx";
import { AUTH_MODAL_ROUTES } from "../../common/helpers/commonConstants.ts";

const AuthModalManager = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { triggerRef } = useTriggerRef();

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
          title: "Login",
          component: <LoginModal onClose={handleClose} />,
        };
      case Path.signUp:
        return {
          title: "Sign Up",
          component: <SignUpModal />,
        };
      case Path.passwordReset:
        return {
          title: "Reset Password",
          component: <ForgotPasswordModal />,
        };
      default:
        return null;
    }
  }, [location.pathname]);

  const isModalOpen = AUTH_MODAL_ROUTES.includes(location.pathname);

  if (!isModalOpen || !modalContent || !triggerRef?.current) return null;

  return (
    <ModalWrapper
      title={modalContent.title}
      cutoutPosition="top-right"
      cutoutOffsetY={15}
      triggerElement={triggerRef.current}
      isOpen={isModalOpen}
      onClose={handleClose}
    >
      {modalContent.component}
    </ModalWrapper>
  );
};

export default AuthModalManager;
