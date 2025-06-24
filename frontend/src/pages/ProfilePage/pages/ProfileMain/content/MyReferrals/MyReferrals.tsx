import { useSelector } from "react-redux";
import { useTranslation } from "react-i18next";
import {
  AppDispatchType,
  AppRootStateType,
} from "../../../../../../store/store";
import { useEffect } from "react";
import { getMyReferrals } from "../../../../../../store/actions/userActions";
import { useDispatch } from "react-redux";
import Table from "../../../../../../components/ui/Table/Table";

const MyReferrals: React.FC = () => {
  const dispatch = useDispatch<AppDispatchType>();
  const referrals = useSelector(
    (state: AppRootStateType) => state.user.referrals
  );

  const { t } = useTranslation();

  useEffect(() => {
    dispatch(getMyReferrals());
  }, []);

  return (
    <Table
      title={t("profile.invited")}
      data={referrals}
      columnLabels={{
        email: t("profile.myReferrals.email"),
        total_paid: t("profile.myReferrals.totalPaid"),
        total_cashback: t("profile.myReferrals.totalCashback"),
      }}
    />
  );
};

export default MyReferrals;
