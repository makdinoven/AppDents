import s from "./Settings.module.scss";
import { Trans } from "react-i18next";
import { PasswordResetForm } from "@/features/change-password";

const Settings = () => {
  return (
    <div>
      <div className={s.settings}>
        <p className={s.section_title}>
          <Trans i18nKey="resetPassword" />
        </p>

        <PasswordResetForm />
      </div>
    </div>
  );
};

export default Settings;
