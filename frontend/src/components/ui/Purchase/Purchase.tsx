import {
  UserPlusIcon,
  TouchCoinIcon,
  CoinIcon,
  CashbackIcon,
} from "../../../assets/logos/index";
import { formatIsoToLocalDatetime } from "../../../common/helpers/helpers";
import s from "./Purchase.module.scss";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { Path } from "../../../routes/routes";

const Purchase = ({ content }: { content: any }) => {
  const { t } = useTranslation();

  const isReferral = !!content.email;

  const renderReferralInfo = () => (
    <p>
      <span className={s.purchase_info_field}>{t("profile.user")}</span>{" "}
      {content.email}
    </p>
  );

  const renderTransactionInfo = () => {
    const { type, amount, meta, slug, landing_name: landingName } = content;

    if (type === "purchase" || type === "internalPurchase") {
      if (slug && landingName) {
        return slug === "CART" ? (
          <p>{t("profile.purchaseHistory.fromCart").toUpperCase()}</p>
        ) : (
          <Link
            to={`/${Path.landingClient}/${slug}`}
            className={s.landing_name}
          >
            {landingName.toUpperCase()}
          </Link>
        );
      }
    }

    if (type === "referralCashback") {
      return (
        <p>
          <span className={s.purchase_info_field}>{t("profile.user")}</span>{" "}
          {meta.email}
        </p>
      );
    }

    if (type === "adminAdjust") {
      return (
        <p>
          <span className={s.purchase_info_field}>
            {t("profile.purchaseHistory.transactionType")}
          </span>{" "}
          {t(
            amount < 0
              ? "profile.purchaseHistory.withdrawal"
              : "profile.purchaseHistory.adjunction"
          )}
        </p>
      );
    }

    return null;
  };

  const renderPurchaseSum = () => {
    const { amount, type, total_cashback: totalCashback } = content;
    const isPositive = amount > 0;

    return (
      <div
        className={`${s.purchase_details_container} ${s.purchase_sum_details}`}
      >
        <span
          className={`${s.purchase_sum} ${
            isPositive || isReferral ? s.adjunction : s.withdrawal
          }`}
        >
          {isReferral
            ? `+${totalCashback}$`
            : isPositive
              ? `+${amount}$`
              : `${amount}$`}
        </span>
        {!isPositive && type === "internalPurchase" && (
          <span>{t("profile.purchaseHistory.fromBalance")}</span>
        )}
        {isReferral && (
          <span>
            {t("profile.referrals.totalCashback").toLowerCase()}
          </span>
        )}
      </div>
    );
  };

  const renderOperationIcon = () => {
    const { type } = content;

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
    <li className={s.purchase}>
      {renderOperationIcon()}
      <div className={s.purchase_content}>
        <div className={s.purchase_info_container}>
          <p className={s.purchase_type}>
            {t(
              isReferral
                ? "profile.referrals.invited"
                : `profile.purchaseHistory.${content.type}`
            )}
          </p>
          <div className={s.purchase_info}>
            {isReferral ? renderReferralInfo() : renderTransactionInfo()}
          </div>
        </div>
        <div className={s.purchase_details_container}>
          {renderPurchaseSum()}
          {content.created_at && formatIsoToLocalDatetime(content.created_at)}
        </div>
      </div>
    </li>
  );
};

export default Purchase;
