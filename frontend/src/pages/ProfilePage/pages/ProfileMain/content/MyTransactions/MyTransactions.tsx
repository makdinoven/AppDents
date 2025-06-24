import { useSelector } from "react-redux";
import { useTranslation } from "react-i18next";
import {
  AppDispatchType,
  AppRootStateType,
} from "../../../../../../store/store";
import { useEffect } from "react";
import { getMyTransactions } from "../../../../../../store/actions/userActions";
import { useDispatch } from "react-redux";
import Table from "../../../../../../components/ui/Table/Table";
import { TransactionType } from "../../../../../../common/types/commonTypes";

const MyTransactions: React.FC = () => {
  const dispatch = useDispatch<AppDispatchType>();
  const transactions = useSelector(
    (state: AppRootStateType) => state.user.transactions
  );

  const { t } = useTranslation();

  useEffect(() => {
    dispatch(getMyTransactions());
  }, []);

  const transactionsAdminAdjust = transactions.filter(
    (transaction) => transaction.type === "adminAdjust"
  );

  const transactionsReferralCashback = transactions.filter(
    (transaction) => transaction.type === "referralCashback"
  );

  const transactionsInternalPurchase = transactions.filter(
    (transaction) => transaction.type === "internalPurchase"
  );

  const handleTableDataTranslate = (tableData: TransactionType[]): any => {
    return tableData.map((tableRow) => {
      return Object.fromEntries(
        Object.entries(tableRow).map(([key, value]) => {
          if (key === "created_at") {
            return [key, value];
          } else if (typeof value === "object") {
            return [key, value?.join(", ")];
          } else {
            return [
              key,
              typeof value === "string"
                ? t(`profile.myTransactions.${value}`)
                : value,
            ];
          }
        })
      );
    });
  };

  return (
    <>
      <Table
        title={t("profile.payments")}
        data={handleTableDataTranslate(transactionsAdminAdjust)}
        columnLabels={{
          amount: t("profile.myTransactions.amount"),
          type: t("profile.myTransactions.type"),
          created_at: t("profile.myTransactions.date"),
          reason: t("profile.myTransactions.reason"),
        }}
      />
      <Table
        data={handleTableDataTranslate(transactionsReferralCashback)}
        columnLabels={{
          amount: t("profile.myTransactions.amount"),
          type: t("profile.myTransactions.type"),
          created_at: t("profile.myTransactions.date"),
          from_user: t("profile.myTransactions.fromUser"),
        }}
      />
      <Table
        data={handleTableDataTranslate(transactionsInternalPurchase)}
        columnLabels={{
          amount: t("profile.myTransactions.amount"),
          type: t("profile.myTransactions.type"),
          created_at: t("profile.myTransactions.date"),
          reason: t("profile.myTransactions.reason"),
          courses: t("profile.myTransactions.courses"),
        }}
      />
    </>
  );
};

export default MyTransactions;
