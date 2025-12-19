import { useTranslation } from "react-i18next";
import { useEffect, useState } from "react";
import { userApi } from "../../shared/api/userApi/userApi.ts";
import { Alert } from "../../shared/components/ui/Alert/Alert.tsx";
import PurchaseTable from "./modules/PurchaseTable/PurchaseTable.tsx";
import { getCamelCaseString } from "../../shared/common/helpers/helpers.ts";
import { AlertCirceIcon } from "../../shared/assets/icons";
import PurchaseItemSkeleton from "../../shared/components/ui/Skeletons/PurchaseItemSkeleton/PurchaseItemSkeleton.tsx";

const PurchaseHistory: React.FC = () => {
  const [transactions, setTransactions] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const { t } = useTranslation();

  useEffect(() => {
    fetchPurchaseHistoryData();
  }, []);

  const fetchPurchaseHistoryData = async () => {
    setLoading(true);
    try {
      const transRes = await userApi.getMyTransactions();

      setTransactions([
        ...transRes.data
          .filter((transaction: any) => {
            return transaction.type !== "REFERRAL_CASHBACK";
          })
          .map((transaction: any) => {
            return {
              ...transaction,
              type: getCamelCaseString(transaction.type),
              meta: transaction.meta,
            };
          }),
      ]);
    } catch {
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

  return loading ? (
    <PurchaseItemSkeleton />
  ) : (
    <PurchaseTable
      content={mergeTransactions(transactions)}
      title={t("profile.purchaseHistory.purchases")}
    />
  );
};

export default PurchaseHistory;
