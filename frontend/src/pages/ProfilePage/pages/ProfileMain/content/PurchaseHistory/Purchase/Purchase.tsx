import {
  CashbackIcon,
  CoinIcon,
  TouchCoinIcon,
  UserPlusIcon,
} from "../../../../../../../assets/icons/index";
import { formatIsoToLocalDatetime } from "../../../../../../../common/helpers/helpers";
import s from "./Purchase.module.scss";
import { Trans, useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";
import { Path } from "../../../../../../../routes/routes";
import ExpandableText from "../../../../../../../components/ui/ExpandableText/ExpandableText";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../../../../../store/store";

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
  const navigate = useNavigate();
  const { language } = useSelector((state: AppRootStateType) => state.user);

  const renderReferralInfo = (contentUnit: any) => (
    <>
      <span className={s.purchase_info_field}>{t("profile.user")}</span>
      {contentUnit.email}
    </>
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
              <ExpandableText
                text={
                  <Link
                    to={`/${Path.landingClient}/${slug}`}
                    className={s.landing_name}
                  >
                    {landingName.toUpperCase()}
                  </Link>
                }
                textClassName={s.exp_text}
                lines={3}
                color="primary"
              />
            );
          } else {
            return (
              <ExpandableText
                text={landingName.toUpperCase()}
                lines={3}
                textClassName={s.exp_text}
                color="primary"
              />
            );
          }
        }
      }
    }

    if (type === "internalPurchase") {
      if (landingName) {
        if (slug) {
          return (
            <ExpandableText
              text={
                <Link
                  to={`/${Path.landingClient}/${slug}`}
                  className={s.landing_name}
                >
                  {landingName.toUpperCase()}
                </Link>
              }
              lines={3}
              textClassName={s.exp_text}
              color="primary"
            />
          );
        } else {
          return (
            <ExpandableText
              text={landingName.toUpperCase()}
              lines={3}
              textClassName={s.exp_text}
              color="primary"
            />
          );
        }
      }
    }

    if (type === "referralCashback") {
      return (
        <>
          <span className={s.purchase_info_field}>{t("profile.user")}</span>{" "}
          {email}
        </>
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
            <div>
              {t("profile.referrals.totalCashback")
                .split(" ")
                .map((value, index) => {
                  return <p key={index}>{value}</p>;
                })}
            </div>
          </>
        ) : (
          <span
            className={`${s.purchase_sum} ${isPositiveAmount ? s.adjunction : s.withdrawal}`}
          >
            {fromBalanceAmount ? (
              <>
                <p className={s.balance}>
                  <span className={s.from_balance}>
                    {t("profile.purchaseHistory.fromBalance")}
                  </span>
                  {fromBalanceAmount}$
                </p>
                <p>{amount}$</p>
              </>
            ) : (
              <p className={s.balance}>
                {type === "internalPurchase" && (
                  <span className={s.from_balance}>
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
      {content.length > 0 ? (
        <div className={s.purchases_container}>
          {content.map((contentUnit: any, index) => {
            return (
              <li key={index} className={s.purchase}>
                {renderOperationIcon(contentUnit)}
                <div className={s.purchase_content}>
                  <div className={s.purchase_info_container}>
                    <p className={s.purchase_type}>
                      {t(
                        isReferral
                          ? "profile.referrals.invitation"
                          : `profile.purchaseHistory.${contentUnit.type}`,
                      )}
                    </p>
                    <div
                      className={s.purchase_info}
                      lang={language.toLowerCase()}
                    >
                      {isReferral
                        ? renderReferralInfo(contentUnit)
                        : renderTransactionInfo(contentUnit)}
                    </div>
                  </div>
                  <div className={s.purchase_details_container}>
                    {renderPurchaseSum(contentUnit)}
                    {contentUnit.created_at && (
                      <div className={s.purchase_date}>
                        {formatIsoToLocalDatetime(contentUnit.created_at, true)
                          .split(" ")
                          .map((value, index) => {
                            return <span key={index}>{value}</span>;
                          })}
                      </div>
                    )}
                  </div>
                </div>
              </li>
            );
          })}
        </div>
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

export default Purchase;
