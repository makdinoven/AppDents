import { Trans } from "react-i18next";
import s from "./PaymentPage.module.scss";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../shared/store/store.ts";
import { useEffect, useRef } from "react";
import {
  BooksIcon,
  CoursesIcon,
  Mail,
  PoweredByStripeLogo,
  Shield,
} from "../../shared/assets/icons";
import LogoList from "./content/LogoList/LogoList.tsx";
import useOutsideClick from "../../shared/common/hooks/useOutsideClick.ts";
import ModalOverlay from "../../shared/components/Modals/ModalOverlay/ModalOverlay.tsx";
import ModalCloseButton from "../../shared/components/ui/ModalCloseButton/ModalCloseButton.tsx";
import UseBalanceOption from "../../shared/components/ui/UseBalanceOption/UseBalanceOption.tsx";
import { usePayment } from "../../shared/common/hooks/usePayment.tsx";
import PaymentForm from "./content/PaymentForm/PaymentForm.tsx";
import Button from "../../shared/components/ui/Button/Button.tsx";
import DisabledPaymentWarn from "../../shared/components/ui/DisabledPaymentBanner/DisabledPaymentWarn/DisabledPaymentWarn.tsx";
import {
  PaymentDataModeType,
  usePaymentPageHandler,
} from "../../shared/common/hooks/usePaymentPageHandler.ts";
import { getLandingDataForPayment } from "../../shared/store/actions/paymentActions.ts";
import { useLocation } from "react-router-dom";
import PaymentItemCard from "./content/PaymentItemCard/PaymentItemCard.tsx";
import { PATHS } from "../../app/routes/routes.ts";

const PaymentPage = () => {
  const validateRef = useRef<() => Promise<boolean>>(null);
  const location = useLocation();
  const dispatch = useDispatch<AppDispatchType>();
  const {
    isPaymentModalOpen,
    paymentModalType,
    closePaymentModal,
    slug,
    paymentModalMode,
  } = usePaymentPageHandler();
  const { data: hookPaymentData, render: renderPaymentData } = useSelector(
    (state: AppRootStateType) => state.payment,
  );
  const closeModalRef = useRef<() => void>(null);
  const { isLogged, email } = useSelector(
    (state: AppRootStateType) => state.user,
  );
  const modalRef = useRef<HTMLDivElement | null>(null);
  const isWebinar = paymentModalType === "webinar";
  const isFree = paymentModalType === "free";
  const isOffer = paymentModalType === "offer";
  const isFromPromotionLanding =
    (location.pathname.includes(PATHS.LANDING.clearPattern) &&
      !location.pathname.includes(PATHS.LANDING_CLIENT.clearPattern) &&
      !location.pathname.includes(PATHS.COURSES_LISTING)) ||
    (location.pathname.includes(PATHS.BOOK_LANDING.clearPattern) &&
      !location.pathname.includes(PATHS.BOOK_LANDING_CLIENT.clearPattern) &&
      !location.pathname.includes(PATHS.BOOKS_LISTING));

  let paymentModeIcon;

  switch (paymentModalMode) {
    case "COURSES":
      paymentModeIcon = <CoursesIcon />;
      break;
    case "BOOKS":
      paymentModeIcon = <BooksIcon />;
      break;
    case "BOTH":
      paymentModeIcon = (
        <div className={s.both_icons}>
          <BooksIcon />
          <CoursesIcon />
        </div>
      );
      break;
    default:
      paymentModeIcon = <CoursesIcon />;
  }

  const {
    loading,
    isBalanceUsed,
    balancePrice,
    balance,
    toggleBalance,
    handlePayment,
    setEmailValue,
    language,
    IS_PAYMENT_DISABLED,
  } = usePayment({
    paymentData: hookPaymentData!,
    isFree,
    isOffer,
  });

  useOutsideClick(modalRef, () => {
    closeModal();
  });

  useEffect(() => {
    if (!hookPaymentData && slug && isPaymentModalOpen) {
      dispatch(
        getLandingDataForPayment({
          slug: slug,
          mode: paymentModalMode as PaymentDataModeType,
        }),
      );
    }
  }, [slug, hookPaymentData, isPaymentModalOpen]);

  const closeModal = () => {
    closePaymentModal();
    closeModalRef.current?.();
  };

  const safeHandlePayment = async () => {
    // Если пользователь не залогинен — сначала валидируем email
    if (!isLogged) {
      const ok = await validateRef.current?.();
      if (!ok) return; // форма не валидна — не дергаем оплату
    }
    handlePayment();
  };

  if (!hookPaymentData || !renderPaymentData) return null;

  const paymentItemsLength = renderPaymentData.items.length;

  const renderHeader = () => (
    <div className={s.modal_header}>
      <ModalCloseButton className={s.close_button} onClick={closeModal} />
      <h2>
        <Trans
          i18nKey={`${isFree && !isLogged ? "freeCourse.registerToWatch" : "yourOrder"}`}
        />
      </h2>
      <div className={s.courses_icon_wrapper}>
        {paymentModeIcon}

        {paymentItemsLength > 0 && (
          <span className={s.circle}>{paymentItemsLength}</span>
        )}
      </div>
    </div>
  );

  const renderCourses = () => (
    <div className={s.courses}>
      {renderPaymentData.items.map((item, index: number) => (
        <PaymentItemCard
          language={language}
          key={index}
          item={item.data}
          itemType={item.item_type}
          isWebinar={isWebinar}
          isFree={isFree}
        />
      ))}
    </div>
  );

  const renderBody = () => (
    <div className={s.modal_body}>
      <div
        className={`${s.total_container} ${!isLogged || isFromPromotionLanding ? s.center : ""}`}
      >
        {!isFree && (
          <div className={s.total_text}>
            <Trans i18nKey="cart.total" />:
            <div>
              <span className={"highlight"}>
                ${isBalanceUsed ? balancePrice : renderPaymentData.new_price}
              </span>
              <span className={`${s.old_price} crossed`}>
                ${renderPaymentData.old_price}
              </span>
            </div>
          </div>
        )}
        {isLogged && !isFree && !isFromPromotionLanding && (
          <UseBalanceOption
            onToggle={toggleBalance}
            isChecked={isBalanceUsed}
            disabled={balance === 0}
            balance={balance ? balance : 0}
          />
        )}
      </div>

      {!isLogged && (
        <PaymentForm
          setEmail={setEmailValue}
          isLogged={isLogged}
          isFree={isFree}
          onRegisterValidate={(fn) => (validateRef.current = fn)} // <— ДОБАВИЛИ
        />
      )}

      {isLogged && isFromPromotionLanding && (
        <PaymentForm setEmail={setEmailValue} isLogged={isLogged} />
      )}
    </div>
  );

  const renderFooter = () => (
    <div className={s.modal_footer}>
      {!isFree && isLogged ? (
        <p lang={language.toLowerCase()} className={s.stripe_text}>
          <Shield className={s.shield_logo} />
          <Trans i18nKey="payment.encryptedPayment" />
        </p>
      ) : (
        <p lang={language.toLowerCase()} className={s.after_payment_text}>
          <Trans i18nKey="payment.afterPayment" />
        </p>
      )}
      {IS_PAYMENT_DISABLED && <DisabledPaymentWarn />}
      {isLogged && (
        <p className={s.email_container}>
          <Mail />
          <span>
            <Trans i18nKey="profile.referrals.email" />:
          </span>
          {email}
        </p>
      )}
      <Button
        onClick={safeHandlePayment}
        disabled={IS_PAYMENT_DISABLED}
        variant={IS_PAYMENT_DISABLED ? "disabled" : "filled"}
        loading={loading}
        text={isFree ? "tryCourseForFree" : balancePrice === 0 ? "get" : "pay"}
        iconRight={isFree ? null : <PoweredByStripeLogo />}
        className={s.payment_btn}
      />
      {!isLogged && (
        <div
          lang={language.toLowerCase()}
          className={`${s.footer_text} ${isFree ? s.free : ""}`}
        >
          {!isFree && (
            <p className={s.stripe_text}>
              <Shield className={s.shield_logo} />
              <Trans i18nKey="payment.encryptedPayment" />
            </p>
          )}
          <p className={s.privacy_text}>
            <Trans
              i18nKey={isFree ? "freePaymentWarn" : "payment.privacyAgreement"}
              components={{
                1: (
                  <a
                    href={PATHS.INFO_PRIVACY}
                    target="_blank"
                    rel="noopener noreferrer"
                  ></a>
                ),
              }}
            />
          </p>
        </div>
      )}
      {!isFree && <LogoList />}
    </div>
  );

  return (
    <ModalOverlay
      isVisibleCondition={isPaymentModalOpen}
      modalPosition="top"
      customHandleClose={closePaymentModal}
      onInitClose={(fn) => (closeModalRef.current = fn)}
    >
      <div ref={modalRef} className={s.modal}>
        {renderHeader()}
        {renderCourses()}
        {renderBody()}
        {renderFooter()}
      </div>
    </ModalOverlay>
  );
};

export default PaymentPage;
