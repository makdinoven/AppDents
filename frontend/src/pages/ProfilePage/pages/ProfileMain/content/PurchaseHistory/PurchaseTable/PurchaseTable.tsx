import { Trans } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Path } from "../../../../../../../routes/routes";
import PurchaseItem from "./PurchaseItem/PurchaseItem";
import s from "./PurchaseTable.module.scss";

type PurchaseTableProps = {
  content: any[];
  isReferral?: boolean;
  title: string;
};

const PurchaseTable = ({ content, isReferral, title }: PurchaseTableProps) => {
  const navigate = useNavigate();

  return (
    <div className={s.table_container}>
      <h3 className={s.container_title}>{title}</h3>
      {content.length > 0 ? (
        <ul className={s.table}>
          {content.map((item, i) => (
            <PurchaseItem key={i} item={item} isReferral={isReferral} />
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
                    onClick={() => navigate(Path.courses)}
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
