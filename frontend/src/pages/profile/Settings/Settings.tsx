import s from "./Settings.module.scss";
import { Trans } from "react-i18next";
import { PasswordResetForm } from "@/features/change-password";
import { t } from "i18next";

const Settings = () => {
  return (
    <div className={s.settings_page}>
      <p className={s.page_title}>{t("profile.settings")}</p>
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
