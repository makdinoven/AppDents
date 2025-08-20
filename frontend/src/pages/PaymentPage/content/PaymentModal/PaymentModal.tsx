import { Trans } from "react-i18next";
import s from "./PaymentModal.module.scss";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../../store/store.ts";
import { useRef } from "react";
import { Path } from "../../../../routes/routes.ts";
import {
  CoursesIcon,
  PoweredByStripeLogo,
  Shield,
} from "../../../../assets/icons";
import { PaymentDataType } from "../../../../store/slices/paymentSlice.ts";
import LogoList from "./LogoList/LogoList.tsx";
import PaymentCourseCard from "./PaymentCourseCard/PaymentCourseCard.tsx";
import useOutsideClick from "../../../../common/hooks/useOutsideClick.ts";
import ModalOverlay from "../../../../components/Modals/ModalOverlay/ModalOverlay.tsx";
import ModalCloseButton from "../../../../components/ui/ModalCloseButton/ModalCloseButton.tsx";
import UseBalanceOption from "../../../../components/ui/UseBalanceOption/UseBalanceOption.tsx";
import { usePaymentModal } from "../../../../common/hooks/usePaymentModal.ts";
import PaymentForm from "./PaymentForm/PaymentForm.tsx";
import Button from "../../../../components/ui/Button/Button.tsx";
import DisabledPaymentWarn from "../../../../components/ui/DisabledPaymentBanner/DisabledPaymentWarn/DisabledPaymentWarn.tsx";
import { usePaymentModalHandler } from "../../../../common/hooks/usePaymentModalHandler.ts";

const PaymentModal = ({
  isOffer = false,
  isWebinar = false,
  isFree = false,
  paymentData,
  visibleCondition,
}: {
  isWebinar?: boolean;
  isFree?: boolean;
  isOffer?: boolean;
  paymentData: PaymentDataType;
  visibleCondition: boolean;
}) => {
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
  } = usePaymentModal({
    paymentData,
    isFree,
    isOffer,
  });
  const { closePaymentModal } = usePaymentModalHandler();
  const closeModalRef = useRef<() => void>(null);
  const { isLogged } = useSelector((state: AppRootStateType) => state.user);
  const modalRef = useRef<HTMLDivElement | null>(null);
  useOutsideClick(modalRef, () => {
    closeModal();
  });

  const closeModal = () => {
    closePaymentModal();
    closeModalRef.current?.();
  };

  return (
    <ModalOverlay
      isVisibleCondition={visibleCondition}
      modalPosition="top"
      onInitClose={(fn) => (closeModalRef.current = fn)}
    >
      <div ref={modalRef} className={s.modal}>
        <div className={s.modal_header}>
          <ModalCloseButton className={s.close_button} onClick={closeModal} />
          <h2>
            <Trans i18nKey={"yourOrder"} />
          </h2>
          <div className={s.courses_icon_wrapper}>
            <CoursesIcon />
            {paymentData.courses.length > 0 && (
              <span className={s.circle}>{paymentData.courses.length}</span>
            )}
          </div>
        </div>
        <div className={s.courses}>
          {paymentData.courses.map((course, index: number) => (
            <PaymentCourseCard
              key={index}
              course={course}
              isWebinar={isWebinar}
              isFree={isFree}
            />
          ))}
        </div>
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
            {isFree && !isLogged && (
              <h3 className={s.total_text}>
                <Trans i18nKey={"freeCourse.registerToWatch"} />
              </h3>
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
        <div className={s.modal_footer}>
          {!isFree && (
            <p lang={language.toLowerCase()} className={s.stripe_text}>
              <Shield />
              <Trans i18nKey="payment.encryptedPayment" />
            </p>
          )}
          {IS_PAYMENT_DISABLED && <DisabledPaymentWarn />}
          <Button
            onClick={handlePayment}
            disabled={IS_PAYMENT_DISABLED}
            variant={IS_PAYMENT_DISABLED ? "disabled" : "filled"}
            loading={loading}
            text={
              isFree ? "tryCourseForFree" : balancePrice === 0 ? "get" : "pay"
            }
            icon={isFree ? undefined : <PoweredByStripeLogo />}
          />
          {!isLogged && (
            <>
              <p className={s.privacy_text}>
                <Trans
                  i18nKey={
                    isFree ? "freePaymentWarn" : "payment.privacyAgreement"
                  }
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
              {!isFree && (
                <p className={s.after_payment_text}>
                  <Trans i18nKey="payment.afterPayment" />
                </p>
              )}
            </>
          )}
          {!isFree && <LogoList />}
        </div>
      </div>
    </ModalOverlay>
  );
};

export default PaymentModal;
