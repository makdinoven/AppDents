import s from "./ProfilePageTitle.module.scss";
import { Trans } from "react-i18next";

export const ProfilePageTitle = ({ title }: { title: string }) => {
  return (
    <div className={s.title}>
      <h3 className={s.title_text}>
        <Trans i18nKey={title} />
      </h3>
    </div>
  );
};
