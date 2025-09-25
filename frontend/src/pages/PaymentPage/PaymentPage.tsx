import { Trans } from "react-i18next";
import s from "./PaymentPage.module.scss";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../store/store.ts";
import { useEffect, useRef } from "react";
import { Path } from "../../routes/routes.ts";
import { CoursesIcon, PoweredByStripeLogo, Shield } from "../../assets/icons";
import LogoList from "./content/LogoList/LogoList.tsx";
import PaymentCourseCard from "./content/PaymentCourseCard/PaymentCourseCard.tsx";
import useOutsideClick from "../../common/hooks/useOutsideClick.ts";
import ModalOverlay from "../../components/Modals/ModalOverlay/ModalOverlay.tsx";
import ModalCloseButton from "../../components/ui/ModalCloseButton/ModalCloseButton.tsx";
import UseBalanceOption from "../../components/ui/UseBalanceOption/UseBalanceOption.tsx";
import { usePayment } from "../../common/hooks/usePayment.ts";
import PaymentForm from "./content/PaymentForm/PaymentForm.tsx";
import Button from "../../components/ui/Button/Button.tsx";
import DisabledPaymentWarn from "../../components/ui/DisabledPaymentBanner/DisabledPaymentWarn/DisabledPaymentWarn.tsx";
import { usePaymentPageHandler } from "../../common/hooks/usePaymentPageHandler.ts";
import { getLandingDataForPayment } from "../../store/actions/paymentActions.ts";

const PaymentPage = () => {
  const dispatch = useDispatch<AppDispatchType>();
  const { isPaymentModalOpen, paymentModalType, closePaymentModal, slug } =
    usePaymentPageHandler();
  const paymentData = useSelector(
    (state: AppRootStateType) => state.payment.data,
  );
  const closeModalRef = useRef<() => void>(null);
  const { isLogged } = useSelector((state: AppRootStateType) => state.user);
  const modalRef = useRef<HTMLDivElement | null>(null);
  const isWebinar = paymentModalType === "webinar";
  const isFree = paymentModalType === "free";
  const isOffer = paymentModalType === "offer";
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
    paymentData,
    isFree,
    isOffer,
  });

  useOutsideClick(modalRef, () => {
    closeModal();
  });

  useEffect(() => {
    if (!paymentData && slug && isPaymentModalOpen) {
      dispatch(getLandingDataForPayment(slug));
    }
  }, [slug, paymentData, isPaymentModalOpen]);

  const closeModal = () => {
    closePaymentModal();
    closeModalRef.current?.();
  };

  if (!paymentData) return null;

  const renderHeader = () => (
    <div className={s.modal_header}>
      <ModalCloseButton className={s.close_button} onClick={closeModal} />
      <h2>
        <Trans
          i18nKey={`${isFree && !isLogged ? "freeCourse.registerToWatch" : "yourOrder"}`}
        />
      </h2>
      <div className={s.courses_icon_wrapper}>
        <CoursesIcon />
        {paymentData.courses.length > 0 && (
          <span className={s.circle}>{paymentData.courses.length}</span>
        )}
      </div>
    </div>
  );

  const renderCourses = () => (
    <div className={s.courses}>
      {paymentData.courses.map((course, index: number) => (
        <PaymentCourseCard
          language={language}
          key={index}
          course={course}
          isWebinar={isWebinar}
          isFree={isFree}
        />
      ))}
    </div>
  );

  const renderBody = () => (
    <div className={s.modal_body}>
      <div className={`${s.total_container} ${!isLogged ? s.center : ""}`}>
        {!isFree && (
          <div className={s.total_text}>
            <Trans i18nKey="cart.total" />:
            <div>
              <span className={"highlight"}>
                ${isBalanceUsed ? balancePrice : paymentData.newPrice}
              </span>
              <span className={`${s.old_price} crossed`}>
                ${paymentData.oldPrice}
              </span>
            </div>
          </div>
        )}
        {isLogged && !isFree && (
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
        />
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
      <Button
        onClick={handlePayment}
        disabled={IS_PAYMENT_DISABLED}
        variant={IS_PAYMENT_DISABLED ? "disabled" : "filled"}
        loading={loading}
        text={isFree ? "tryCourseForFree" : balancePrice === 0 ? "get" : "pay"}
        icon={isFree ? undefined : <PoweredByStripeLogo />}
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
                    href={Path.privacyPolicy}
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
        {!isFree && renderBody()}
        {renderFooter()}
      </div>
    </ModalOverlay>
  );
};

export default PaymentPage;
