import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import s from "./PurchaseItem.module.scss";
import { AppRootStateType } from "../../../../../../../../store/store.ts";
import {
  BooksIcon,
  CashbackIcon,
  CoinIcon,
  CoursesIcon,
  TouchCoinIcon,
  UserPlusIcon,
} from "../../../../../../../../assets/icons";
import ExpandableText from "../../../../../../../../components/ui/ExpandableText/ExpandableText.tsx";
import { Path } from "../../../../../../../../routes/routes.ts";
import { formatIsoToLocalDatetime } from "../../../../../../../../common/helpers/helpers.ts";

type PurchaseItemProps = {
  item: any;
  isReferral?: boolean;
};

const PurchaseItem = ({ item, isReferral }: PurchaseItemProps) => {
  const { t } = useTranslation();
  const { language } = useSelector((state: AppRootStateType) => state.user);

  const {
    type,
    meta,
    slug,
    landing_name,
    book_landing_name,
    book_landing_slug,
    email,
    amount,
    total_cashback: totalCashback,
    fromBalanceAmount,
    created_at,
  } = item;

  const isBook = !landing_name && book_landing_name;
  const showProductIcon = type === "purchase" || type === "internalPurchase";
  const landingName = landing_name ? landing_name : book_landing_name;
  const landingSlug = slug ? slug : book_landing_slug;

  const icon = (() => {
    if (isReferral) return <UserPlusIcon className={s.icon} />;
    switch (type) {
      case "purchase":
      case "internalPurchase":
        return <CoinIcon className={s.icon} />;
      case "referralCashback":
        return <CashbackIcon className={s.icon} />;
      case "adminAdjust":
        return <TouchCoinIcon className={s.icon} />;
      default:
        return null;
    }
  })();

  // 2. заголовок
  const title = isReferral
    ? t("profile.referrals.invitation")
    : t(`profile.purchaseHistory.${type}`);

  // 3. описание (что именно купили / кого пригласили)
  const description = (() => {
    if (isReferral) {
      return (
        <>
          <span className={s.purchase_info_field}>{t("profile.user")}</span>{" "}
          {email}
        </>
      );
    }

    // покупка
    if (type === "purchase" || type === "internalPurchase") {
      if (landingName) {
        if (meta?.source === "CART") {
          return <p>{t("profile.purchaseHistory.fromCart").toUpperCase()}</p>;
        }
        if (landingSlug) {
          return (
            <ExpandableText
              text={
                <Link
                  to={`${!isBook ? `/${Path.landingClient}` : Path.bookLandingClient}/${landingSlug}`}
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
        }
        return (
          <ExpandableText
            text={landing_name.toUpperCase()}
            lines={3}
            textClassName={s.exp_text}
            color="primary"
          />
        );
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

    return null;
  })();

  // 4. сумма/кастомный блок суммы
  const amountBlock = (() => {
    const isPositiveAmount = typeof amount === "number" ? amount > 0 : false;
    const isPositiveCashback =
      typeof totalCashback === "number" ? totalCashback > 0 : false;

    // рефералка
    if (isReferral) {
      return (
        <div className={s.amount_referral}>
          <span className={isPositiveCashback ? s.plus : s.zero}>
            {totalCashback ? `${totalCashback}$` : "0$"}
          </span>
          <div className={s.amount_caption}>
            {t("profile.referrals.totalCashback")
              .split(" ")
              .map((value, index) => (
                <p key={index}>{value}</p>
              ))}
          </div>
        </div>
      );
    }

    // покупка, но часть списана с баланса
    if (fromBalanceAmount) {
      return (
        <div className={s.amount_balance}>
          <p className={s.balance}>
            <span className={s.from_balance}>
              {t("profile.purchaseHistory.fromBalance")}
            </span>
            {fromBalanceAmount}$
          </p>
          <p className={isPositiveAmount ? s.plus : s.minus}>{amount}$</p>
        </div>
      );
    }

    // обычная покупка / операция
    return (
      <p className={`${s.balance} ${isPositiveAmount ? s.plus : s.minus}`}>
        {type === "internalPurchase" && (
          <span className={s.from_balance}>
            {t("profile.purchaseHistory.fromBalance")}
          </span>
        )}
        {typeof amount === "number"
          ? `${isPositiveAmount ? "+" : ""}${amount}$`
          : amount}
      </p>
    );
  })();

  // 5. футер (дата)
  const footer = (() => {
    if (!created_at) return null;
    const parts = formatIsoToLocalDatetime(created_at, true).split(" ");
    return (
      <div className={s.date}>
        {parts.map((v: string, i: number) => (
          <span key={i}>{v}</span>
        ))}
      </div>
    );
  })();

  return (
    <li lang={language.toLowerCase()} className={s.purchase}>
      {icon}
      <div className={s.content}>
        <div className={s.top}>
          <p className={s.title}>
            {title}
            {showProductIcon && (
              <>
                {isBook ? (
                  <BooksIcon className={s.product_icon} />
                ) : (
                  <CoursesIcon className={s.product_icon} />
                )}
              </>
            )}
          </p>
          {description && <div className={s.description}>{description}</div>}
        </div>
        <div className={s.bottom}>
          {amountBlock && <div className={s.amount}>{amountBlock}</div>}
          {footer && <div className={s.footer}>{footer}</div>}
        </div>
      </div>
    </li>
  );
};

export default PurchaseItem;
