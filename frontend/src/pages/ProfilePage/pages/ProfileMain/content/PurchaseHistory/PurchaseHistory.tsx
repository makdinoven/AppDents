import { useTranslation } from "react-i18next";
import { useEffect, useState } from "react";
import { userApi } from "../../../../../../api/userApi/userApi";
import { Alert } from "../../../../../../components/ui/Alert/Alert";
import s from "./PurchaseHistory.module.scss";
import Purchase from "../../../../../../components/ui/Purchase/Purchase";
import { capitalizeText } from "../../../../../../common/helpers/helpers";
import Loader from "../../../../../../components/ui/Loader/Loader";
import { AlertCirceIcon } from "../../../../../../assets/logos/index";

const PurchaseHistory: React.FC = () => {
  const [referrals, setReferrals] = useState<any[]>([]);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const { t } = useTranslation();

  useEffect(() => {
    fetchPurchaseHistoryData();
  }, []);

  const getCamelCaseString = (string: string): string => {
    return string.split("_").reduce((result, value, index) => {
      return index === 0
        ? result + value.toLowerCase()
        : result + capitalizeText(value);
    }, "");
  };

  const fetchPurchaseHistoryData = async () => {
    setLoading(true);
    try {
      const [refsRes, transRes] = await Promise.all([
        userApi.getMyReferrals(),
        userApi.getMyTransactions(),
      ]);

      setReferrals([...refsRes.data]);
      setTransactions([
        ...transRes.data.map((transaction: any) => {
          return {
            ...transaction,
            type: getCamelCaseString(transaction.type),
            meta: structuredClone(transaction.meta),
          };
        }),
      ]);
    } catch (error: any) {
      Alert(`Error fetching loading data`, <AlertCirceIcon />);
    } finally {
      setLoading(false);
    }
  };

  return loading ? (
    <Loader />
  ) : (
    <div className={s.purchase_history}>
      <h3>{t("profile.purchaseHistory.tabName")}</h3>
      <ul className={s.purchase_history_container}>
        {referrals.map((referral) => (
          <Purchase key={referral.email} content={referral} />
        ))}
        {transactions.map((transaction) => (
          <Purchase key={transaction.id} content={transaction} />
        ))}
      </ul>
    </div>
  );
};

export default PurchaseHistory;
