import { Trans } from "react-i18next";
import { useNavigate } from "react-router-dom";
import s from "./PurchaseTable.module.scss";
import PurchaseItem from "./PurchaseItem/PurchaseItem.tsx";
import { PATHS } from "../../../../app/routes/routes.ts";
import { ProfilePageTitle } from "@/shared/components/ui/profile-page-title/ProfilePageTitle.tsx";

type HistoryTableProps = {
  content: any[];
  isReferral?: boolean;
  title: string;
};

const PurchaseTable = ({ content, isReferral, title }: HistoryTableProps) => {
  const navigate = useNavigate();

  return (
    <div className={s.table_container}>
      <ProfilePageTitle title={title} />
      {content.length > 0 ? (
        <ul className={s.table}>
          {content.map((item, i) => (
            <PurchaseItem key={i} item={item} />
          ))}
        </ul>
      ) : (
        <p className={s.no_data_message}>
          {isReferral ? (
            <Trans i18nKey="profile.purchaseHistory.noReferralsData" />
          ) : (
            <Trans
              i18nKey="profile.purchaseHistory.noPurchasesData"
              components={{
                1: (
                  <span
                    onClick={() => navigate(PATHS.COURSES_LISTING)}
                    className={`${s.no_data_message} ${s.link}`}
                  />
                ),
              }}
            />
          )}
        </p>
      )}
    </div>
  );
};

export default PurchaseTable;
