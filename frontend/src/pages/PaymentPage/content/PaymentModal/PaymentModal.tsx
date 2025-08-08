import { useForm } from "react-hook-form";
import { joiResolver } from "@hookform/resolvers/joi";
import { t } from "i18next";
import { Trans } from "react-i18next";
import s from "./PaymentModal.module.scss";
import Form from "../../../../components/Modals/modules/Form/Form.tsx";
import Button from "../../../../components/ui/Button/Button.tsx";
import { paymentSchema } from "../../../../common/schemas/paymentSchema.ts";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../../../store/store.ts";
import { mainApi } from "../../../../api/mainApi/mainApi.ts";
import { useRef, useState } from "react";
import {
  BASE_URL,
  LS_TOKEN_KEY,
  REF_CODE_LS_KEY,
  REF_CODE_PARAM,
} from "../../../../common/helpers/commonConstants.ts";
import { cartStorage } from "../../../../api/cartApi/cartStorage.ts";
import { useNavigate } from "react-router-dom";
import { Path } from "../../../../routes/routes.ts";
import { PaymentType } from "../../../../api/userApi/types.ts";
import { getMe } from "../../../../store/actions/userActions.ts";
import { Alert } from "../../../../components/ui/Alert/Alert.tsx";
import {
  CheckMark,
  CoursesIcon,
  PoweredByStripeLogo,
  Shield,
} from "../../../../assets/icons";
import DisabledPaymentWarn from "../../../../components/ui/DisabledPaymentBanner/DisabledPaymentWarn/DisabledPaymentWarn.tsx";
import {
  closePaymentModal,
  PaymentDataType,
} from "../../../../store/slices/paymentSlice.ts";
import { getPaymentSource } from "../../../../common/helpers/helpers.ts";
import LogoList from "./LogoList/LogoList.tsx";
import PaymentCourseCard from "./PaymentCourseCard/PaymentCourseCard.tsx";
import Input from "../../../../components/ui/Inputs/Input/Input.tsx";
import EmailInput from "../../../../components/ui/Inputs/EmailInput/EmailInput.tsx";
import useOutsideClick from "../../../../common/hooks/useOutsideClick.ts";
import ModalOverlay from "../../../../components/Modals/ModalOverlay/ModalOverlay.tsx";
import ModalCloseButton from "../../../../components/ui/ModalCloseButton/ModalCloseButton.tsx";
import UseBalanceOption from "../../../../components/ui/UseBalanceOption/UseBalanceOption.tsx";

const PaymentModal = ({
  isOffer = false,
  isWebinar = false,
  isFree = false,
  paymentData,
  visibleCondition,
  handleClose,
}: {
  handleClose: () => void;
  isWebinar?: boolean;
  isFree?: boolean;
  isOffer?: boolean;
  paymentData: PaymentDataType;
  visibleCondition: boolean;
}) => {
  const language = useSelector(
    (state: AppRootStateType) => state.user.language,
  );
  const currentUrl =
    window.location.origin + location.pathname + location.search;
  const IS_PAYMENT_DISABLED = false;
  const navigate = useNavigate();
  const balance = useSelector((state: AppRootStateType) => state.user.balance);
  const [loading, setLoading] = useState(false);
  const dispatch = useDispatch<AppDispatchType>();
  const { isLogged, email } = useSelector(
    (state: AppRootStateType) => state.user,
  );
  const [isBalanceUsed, setIsBalanceUsed] = useState<boolean>(false);
  const {
    register,
    watch,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<PaymentType>({
    resolver: isLogged ? undefined : joiResolver(paymentSchema),
    mode: "onTouched",
  });
  const modalRef = useRef<HTMLDivElement | null>(null);
  useOutsideClick(modalRef, () => {
    closeModal();
  });

  const closeModalRef = useRef<() => void>(null);

  const closeModal = () => {
    closeModalRef.current?.();
    handleClose();
  };

  const emailInputName = "email";
  const emailValue = watch(emailInputName);

  const handleCheckboxToggle = () => {
    if (balance! !== 0) {
      setIsBalanceUsed(!isBalanceUsed);
    }
  };

  const balancePrice = isBalanceUsed
    ? Math.round(Math.max(paymentData.newPrice - balance!, 0) * 100) / 100
    : paymentData.newPrice;

  //TODO ВЫНЕСТИ И ОСТАВИТЬ В ЭТОМ КОМПОНЕНТЕ ТОЛЬКО ЛОГИКУ КАСАЮЩУЮСЯ ОТОБРАЖЕНИЯ

  const handlePayment = async (form: any) => {
    setLoading(true);
    if (!isFree) {
      const rcCode = localStorage.getItem(REF_CODE_LS_KEY);
      const cartLandingIds = cartStorage.getLandingIds();
      const dataToSend = {
        total_old_price: paymentData.oldPrice,
        total_new_price: paymentData.newPrice,
        from_ad: paymentData.fromAd,
        price_cents: paymentData.priceCents,
        region: paymentData.region ? paymentData.region : language,
        landing_ids: paymentData.landingIds,
        course_ids: paymentData.courseIds,
        use_balance: isBalanceUsed,
        user_email: isLogged ? email : form.email,
        transfer_cart: !isLogged && cartLandingIds.length > 0,
        cart_landing_ids: cartLandingIds,
        source: !paymentData.source
          ? getPaymentSource(isOffer)
          : paymentData.source,
        success_url: `${BASE_URL}${Path.successPayment}`,
        courses: paymentData.courses,
        cancel_url:
          !isLogged && rcCode
            ? currentUrl + `?${REF_CODE_PARAM}=${rcCode}`
            : currentUrl,
      };
      try {
        const res = await mainApi.buyCourse(dataToSend, isLogged);
        const checkoutUrl = res.data.checkout_url;
        const balanceLeft = res.data.balance_left;
        localStorage.removeItem(REF_CODE_LS_KEY);
        setLoading(false);

        if (checkoutUrl) {
          const newTab = window.open(checkoutUrl, "_blank");

          if (
            !newTab ||
            newTab.closed ||
            typeof newTab.closed === "undefined"
          ) {
            window.location.href = checkoutUrl;
          }
        } else {
          console.error("Checkout URL is missing");
        }

        if (balanceLeft) {
          dispatch(getMe());
          Alert(
            t("successPaymentWithBalance", { balance: balanceLeft }),
            <CheckMark />,
            () => {
              navigate(Path.profile);
            },
          );
          await dispatch(getMe());
        }
      } catch (error) {
        console.log(error);
      }
    } else {
      const dataToSend = {
        id: paymentData.landingIds![0],
        email: isLogged ? email : form.email,
        region: paymentData.region ? paymentData.region : language,
      };

      try {
        const res = await mainApi.getFreeCourse(dataToSend, isLogged);
        if (isLogged) {
          navigate(Path.profile);
        } else {
          dispatch(closePaymentModal());
          closeModal();
          localStorage.setItem(LS_TOKEN_KEY, res.data.access_token);
          await dispatch(getMe());
          navigate(Path.profile);
        }
        setLoading(false);
      } catch (error) {
        console.log(error);
      }
    }
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
                onToggle={handleCheckboxToggle}
                isChecked={isBalanceUsed}
                disabled={balance === 0}
                balance={balance ? balance : 0}
              />
            )}
          </div>

          {isFree && !isLogged && (
            <h3 className={s.total_text}>
              <Trans i18nKey={"freeCourse.registerToWatch"} />
            </h3>
          )}

          {!isLogged && (
            <>
              <div className={s.form_inputs}>
                <Input
                  id="name"
                  placeholder={t("yourName")}
                  {...register("name")}
                />
                <EmailInput
                  isValidationUsed
                  id="email"
                  value={emailValue}
                  setValue={setValue}
                  error={errors.email?.message}
                  placeholder={t("email")}
                  {...register(emailInputName)}
                />
              </div>
            </>
          )}
        </div>
        <div className={s.modal_footer}>
          {!isFree && (
            <p lang={language.toLowerCase()} className={s.stripe_text}>
              <Shield />
              <Trans i18nKey="payment.encryptedPayment" />
            </p>
          )}

          <Form handleSubmit={handleSubmit(handlePayment)}>
            {IS_PAYMENT_DISABLED && <DisabledPaymentWarn />}
            <Button
              disabled={IS_PAYMENT_DISABLED}
              variant={IS_PAYMENT_DISABLED ? "disabled" : "filled"}
              loading={loading}
              text={
                isFree ? "tryCourseForFree" : balancePrice === 0 ? "get" : "pay"
              }
              type="submit"
              icon={<PoweredByStripeLogo />}
            />
          </Form>
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
