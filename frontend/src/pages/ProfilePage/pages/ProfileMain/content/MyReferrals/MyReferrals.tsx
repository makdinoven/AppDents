import { useTranslation } from "react-i18next";
import s from "./MyReferrals.module.scss";

const MyReferrals: React.FC = () => {
  const { t } = useTranslation();
  return (
    <div className={s.referrals_container}>
      {t("profile.invited").toUpperCase()}
    </div>
  );
};

export default MyReferrals;
