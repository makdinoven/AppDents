import { useTranslation } from "react-i18next";
import { useEffect, useState } from "react";
import { userApi } from "../../../api/userApi/userApi.ts";
import { Alert } from "../../../components/ui/Alert/Alert.tsx";
import PurchaseTable from "./modules/PurchaseTable/PurchaseTable.tsx";
import { getCamelCaseString } from "../../../common/helpers/helpers.ts";
import { AlertCirceIcon } from "../../../assets/icons";
import PurchaseItemSkeleton from "../../../components/ui/Skeletons/PurchaseItemSkeleton/PurchaseItemSkeleton.tsx";

const InvitedUsers: React.FC = () => {
  const [referralsInfo, setReferralsInfo] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const { t } = useTranslation();

  useEffect(() => {
    fetchPurchaseHistoryData();
  }, []);

  const fetchPurchaseHistoryData = async () => {
    setLoading(true);
    try {
      const [refsRes, transRes] = await Promise.all([
        userApi.getMyReferrals(),
        userApi.getMyTransactions(),
      ]);

      const invites = refsRes.data.map((referral: any) => {
        return {
          email: referral.email,
          total_cashback: referral.total_cashback,
          type: "invite",
        };
      });

      const cashbacks = transRes.data
        .filter((transaction: any) => {
          return transaction.type === "REFERRAL_CASHBACK";
        })
        .map((transaction: any) => {
          return {
            email: transaction.email,
            amount: transaction.amount,
            created_at: transaction.created_at,
            type: getCamelCaseString(transaction.type),
          };
        });

      setReferralsInfo([...invites, ...cashbacks]);
    } catch {
      Alert(`Error fetching loading data`, <AlertCirceIcon />);
    } finally {
      setLoading(false);
    }
  };

  return loading ? (
    <PurchaseItemSkeleton />
  ) : (
    <PurchaseTable
      content={referralsInfo}
      title={t("profile.purchaseHistory.invitedUsers")}
      isReferral
    />
  );
};

export default InvitedUsers;
