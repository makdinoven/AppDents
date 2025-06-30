import {
  UserPlusIcon,
  CoinIcon,
  CashbackIcon,
  TouchCoinIcon,
} from "../../../../../../../assets/logos/index/index";
import { formatIsoToLocalDatetime } from "../../../../../../../common/helpers/helpers";
import s from "./Purchase.module.scss";
import { useTranslation, Trans } from "react-i18next";
import { Link } from "react-router-dom";
import { Path } from "../../../../../../../routes/routes";

const Purchase = ({
  content,
  isReferral,
  title,
}: {
  content: any[];
  isReferral?: boolean;
  title: string;
}) => {
  const { t } = useTranslation();

  const renderReferralInfo = (contentUnit: any) => (
    <p>
      <span className={s.purchase_info_field}>{t("profile.user")}</span>{" "}
      {contentUnit.email}
    </p>
  );

  const renderTransactionInfo = (contentUnit: any) => {
    const { type, meta, email, slug, landing_name: landingName } = contentUnit;

    if (type === "purchase") {
      if (landingName) {
        if (meta.source && meta.source === "CART") {
          return <p>{t("profile.purchaseHistory.fromCart").toUpperCase()}</p>;
        } else {
          if (slug) {
            return (
              <Link
                to={`/${Path.landingClient}/${slug}`}
                className={s.landing_name}
              >
                {landingName.toUpperCase()}
              </Link>
            );
          } else {
            return (
              <p className={s.landing_name}>{landingName.toUpperCase()}</p>
            );
          }
        }
      }
    }

    if (type === "internalPurchase") {
      if (landingName) {
        if (slug) {
          return (
            <Link
              to={`/${Path.landingClient}/${slug}`}
              className={s.landing_name}
            >
              {landingName.toUpperCase()}
            </Link>
          );
        } else {
          return <p className={s.landing_name}>{landingName.toUpperCase()}</p>;
        }
      }
    }

    if (type === "referralCashback") {
      return (
        <p>
          <span className={s.purchase_info_field}>{t("profile.user")}</span>{" "}
          {email}
        </p>
      );
    }
  };

  const renderPurchaseSum = (contentUnit: any) => {
    const {
      type,
      amount,
      total_cashback: totalCashback,
      fromBalanceAmount,
    } = contentUnit;
    const isPositiveAmount = amount > 0;
    const isPositiveCashback = totalCashback > 0;

    return (
      <div
        className={`${s.purchase_details_container} ${s.purchase_sum_details}`}
      >
        {isReferral ? (
          <>
            <span
              className={`${s.purchase_sum} ${isPositiveCashback ? s.adjunction : s.no_cashback}`}
            >
              {totalCashback ? `${totalCashback}$` : "0$"}
            </span>
            <span>{t("profile.referrals.totalCashback")}</span>
          </>
        ) : (
          <span
            className={`${s.purchase_sum} ${isPositiveAmount ? s.adjunction : s.withdrawal}`}
          >
            {fromBalanceAmount ? (
              <>
                <p className={s.balance}>
                  <span className={s.purchase_sum}>
                    {t("profile.purchaseHistory.fromBalance")}
                  </span>
                  {fromBalanceAmount}$
                </p>
                <p>{amount}$</p>
              </>
            ) : (
              <p className={s.balance}>
                {type === "internalPurchase" && (
                  <span className={s.purchase_sum}>
                    {t("profile.purchaseHistory.fromBalance")}
                  </span>
                )}
                {`${isPositiveAmount ? "+" : ""}${amount}$`}
              </p>
            )}
          </span>
        )}
      </div>
    );
  };

  const renderOperationIcon = (contentUnit: any) => {
    const { type } = contentUnit;

    if (isReferral) {
      return <UserPlusIcon className={s.purchase_icon} />;
    }
    if (type === "purchase" || type === "internalPurchase") {
      return <CoinIcon className={s.purchase_icon} />;
    } else if (type === "referralCashback") {
      return <CashbackIcon className={s.purchase_icon} />;
    } else if (type === "adminAdjust") {
      return <TouchCoinIcon className={s.purchase_icon} />;
    }
  };

  return (
    <div className={s.purchase_item}>
      <h3 className={s.purchase_item_header}>{title}</h3>
      <div className={s.purchases_container}>
        {content.length > 0 ? (
          content.map((contentUnit: any, index) => {
            return (
              <li key={index} className={s.purchase}>
                {renderOperationIcon(contentUnit)}
                <div className={s.purchase_content}>
                  <div className={s.purchase_info_container}>
                    <p className={s.purchase_type}>
                      {t(
                        isReferral
                          ? "profile.referrals.invited"
                          : `profile.purchaseHistory.${contentUnit.type}`
                      )}
                    </p>
                    <div className={s.purchase_info}>
                      {isReferral
                        ? renderReferralInfo(contentUnit)
                        : renderTransactionInfo(contentUnit)}
                    </div>
                  </div>
                  <div className={s.purchase_details_container}>
                    {renderPurchaseSum(contentUnit)}
                    {contentUnit.created_at &&
                      formatIsoToLocalDatetime(contentUnit.created_at)}
                  </div>
                </div>
              </li>
            );
          })
        ) : (
          <Trans />
        )}
      </div>
    </div>
  );
};

export default Purchase;
