import { useTranslation } from "react-i18next";
import { useEffect, useState } from "react";
import { userApi } from "../../../../../../api/userApi/userApi";

const PurchaseHistory: React.FC = () => {
  const [referrals, setReferrals] = useState<any[]>([]);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const { t } = useTranslation();

  useEffect(() => {
    fetchPurchaseHistoryData();
  }, []);

  const fetchPurchaseHistoryData = async () => {
    try {
      const [refsRes, transRes] = await Promise.all([
        userApi.getMyReferrals(),
        userApi.getMyTransactions(),
      ]);

      setReferrals([...refsRes.data]);
      setTransactions([
        ...transRes.data.map((transaction: any) => ({
          ...transaction,
          meta: structuredClone(transaction.meta),
        })),
      ]);
    } catch (e) {
    } finally {
    }
  };

  return <></>;
};

export default PurchaseHistory;
