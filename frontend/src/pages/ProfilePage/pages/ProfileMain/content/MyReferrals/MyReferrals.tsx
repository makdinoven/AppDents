import { useTranslation } from "react-i18next";
import { useEffect } from "react";
import Table from "../../../../../../components/ui/Table/Table";
import Loader from "../../../../../../components/ui/Loader/Loader.tsx";

const MyReferrals: React.FC = () => {
  const { t } = useTranslation();

  useEffect(() => {}, []);

  return loading ? (
    <Loader />
  ) : (
    <Table
      title={t("profile.invited")}
      showNumberCol={false}
      data={referrals}
      columnLabels={{
        email: t("profile.myReferrals.email"),
        total_cashback: t("profile.myReferrals.totalCashback"),
      }}
    />
  );
};

export default MyReferrals;
