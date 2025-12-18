import s from "./CommonModalStyles.module.scss";
import { useNavigate } from "react-router-dom";
import { PATHS } from "@/app/routes/routes.ts";
import ModalLink from "@/shared/components/Modals/modules/ModalLink/ModalLink.tsx";
import { ForgotPasswordForm } from "@/features/change-password";
import { Trans } from "react-i18next";

const ForgotPasswordModal = () => {
  const navigate = useNavigate();

  return (
    <div className={s.modal}>
      <ForgotPasswordForm
        onSuccess={() => navigate("/login")}
        bottomSlot={(error) => (
          <div className={s.modal_bottom}>
            {error && (
              <p className={s.error_message}>
                <Trans i18nKey={error} />
              </p>
            )}
            <span>
              <Trans i18nKey="passwordResetMailSent" />
            </span>
            <ModalLink link={PATHS.LOGIN} text={"backToLogin"} />
          </div>
        )}
      />
    </div>
  );
};

export default ForgotPasswordModal;
