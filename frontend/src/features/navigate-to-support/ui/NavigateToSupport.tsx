import s from "./NavigateToSupport.module.scss";
import { PATHS } from "@/app/routes/routes.ts";
import { t } from "i18next";
import { Link } from "react-router-dom";
import { Arrow, Support } from "@/shared/assets/icons";
import { Trans } from "react-i18next";

export const NavigateToSupport = () => {
  return (
    <div className={s.navigate_container}>
      <Link to={PATHS.PROFILE_SUPPORT} className={s.navigate_button}>
        <span>
          <Support />
          {t("support.supportCenter")}
        </span>
        <Arrow />
      </Link>
      <div className={s.reserve_email}>
        <Trans i18nKey="support.reserveEmail" />{" "}
        <span>
          <a className={s.mail_link} href="mailto:info.dis.org@gmail.com">
            info.dis.org@gmail.com
          </a>
        </span>
      </div>
    </div>
  );
};
