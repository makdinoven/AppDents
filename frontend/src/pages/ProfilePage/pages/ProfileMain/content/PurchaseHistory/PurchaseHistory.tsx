import { useTranslation } from "react-i18next";
import { useEffect, useState } from "react";
import { userApi } from "../../../../../../api/userApi/userApi";
import { Alert } from "../../../../../../components/ui/Alert/Alert";
import s from "./PurchaseHistory.module.scss";
import Purchase from "./Purchase/Purchase";
import { capitalizeText } from "../../../../../../common/helpers/helpers";
import { AlertCirceIcon } from "../../../../../../assets/icons/index";
import PurchaseHistorySkeleton from "../../../../../../components/ui/Skeletons/PurchaseHistorySkeleton/PurchaseHistorySkeleton";

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
            meta: transaction.meta,
          };
        }),
      ]);
    } catch (error: any) {
      Alert(`Error fetching loading data`, <AlertCirceIcon />);
    } finally {
      setLoading(false);
    }
  };

  const mergeTransactions = (transactions: any[]): any[] => {
    const idMap = new Map<number, any>();
    const merged: any[] = [];
    const registered = new Set<number>();

    for (const trans of transactions) {
      idMap.set(Number(trans.id), trans);
    }

    for (const trans of transactions) {
      const purchaseId =
        trans.meta.purchase_id && Number(trans.meta.purchase_id);

      if (
        trans.type === "internalPurchase" &&
        purchaseId &&
        idMap.has(purchaseId)
      ) {
        const purchase = idMap.get(purchaseId);

        const mergedTrans = {
          ...trans,
          fromBalanceAmount: trans.amount,
          ...purchase,
          amount: purchase.amount,
        };

        merged.push(mergedTrans);
        registered.add(trans.id);
        registered.add(purchase.id);
      } else if (!registered.has(trans.id)) {
        merged.push(trans);
      }
    }

    return merged;
  };

  return (
    <div className={s.purchase_history}>
      {loading ? (
        <PurchaseHistorySkeleton />
      ) : (
        <>
          <Purchase
            content={referrals}
            title={t("profile.purchaseHistory.invitedUsers")}
            isReferral
          />
          <Purchase
            content={mergeTransactions(transactions)}
            title={t("profile.purchaseHistory.purchases")}
          />
        </>
      )}
    </div>
  );
};

export default PurchaseHistory;
