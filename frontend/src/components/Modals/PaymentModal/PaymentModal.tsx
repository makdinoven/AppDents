import { useForm } from "react-hook-form";
import { joiResolver } from "@hookform/resolvers/joi";
import { t } from "i18next";
import { Trans } from "react-i18next";
import s from "./PaymentModal.module.scss";
import Form from "../modules/Form/Form";
import Input from "../modules/Input/Input";
import Button from "../../ui/Button/Button";
import { paymentSchema } from "../../../common/schemas/paymentSchema";
import {
  AmexLogo,
  ApplePayLogo,
  DinnerClubLogo,
  DiscoverLogo,
  GooglePayLogo,
  JcbLogo,
  MastercardLogo,
  PaypalLogo,
  UnionPayLogo,
  VisaLogo,
} from "../../../assets/logos/index";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../../store/store.ts";
import { mainApi } from "../../../api/mainApi/mainApi.ts";
import { useState } from "react";
import ToggleCheckbox from "../../ui/ToggleCheckbox/ToggleCheckbox.tsx";
import {
  BASE_URL,
  LS_TOKEN_KEY,
  REF_CODE_LS_KEY,
  REF_CODE_PARAM,
} from "../../../common/helpers/commonConstants.ts";
import { cartStorage } from "../../../api/cartApi/cartStorage.ts";
import { useNavigate } from "react-router-dom";
import { Path } from "../../../routes/routes.ts";
import { PaymentType } from "../../../api/userApi/types.ts";
import { getMe } from "../../../store/actions/userActions.ts";
import { Alert } from "../../ui/Alert/Alert.tsx";
import CheckMark from "../../../assets/Icons/CheckMark.tsx";
import { PaymentDataType } from "../../../store/slices/paymentSlice.ts";
import { getPaymentSource } from "../../../common/helpers/helpers.ts";

const logos = [
  VisaLogo,
  MastercardLogo,
  ApplePayLogo,
  GooglePayLogo,
  PaypalLogo,
  AmexLogo,
  JcbLogo,
  UnionPayLogo,
  DinnerClubLogo,
  DiscoverLogo,
];

const PaymentModal = ({
  isOffer = false,
  isWebinar = false,
  isFree = false,
  paymentData,
}: {
  isWebinar?: boolean;
  isFree?: boolean;
  isOffer?: boolean;
  paymentData: PaymentDataType;
}) => {
  const language = useSelector(
    (state: AppRootStateType) => state.user.language,
  );
  const currentUrl =
    window.location.origin + location.pathname + location.search;
  const navigate = useNavigate();
  const balance = useSelector((state: AppRootStateType) => state.user.balance);
  const [loading, setLoading] = useState(false);
  const dispatch = useDispatch<AppDispatchType>();
  const { isLogged, email } = useSelector(
    (state: AppRootStateType) => state.user,
  );
  const [isBalanceUsed, setIsBalanceUsed] = useState<boolean>(
    isLogged && balance ? balance > 0 : false,
  );
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<PaymentType>({
    resolver: isLogged ? undefined : joiResolver(paymentSchema),
    mode: "onTouched",
  });

  const handleCheckboxToggle = () => {
    if (balance! !== 0) {
      setIsBalanceUsed(!isBalanceUsed);
    }
  };

  const balancePrice = isBalanceUsed
    ? Math.round(Math.max(paymentData.newPrice - balance!, 0) * 100) / 100
    : paymentData.newPrice;

  const handlePayment = async (form: any) => {
    setLoading(true);
    if (!isFree) {
      const rcCode = localStorage.getItem(REF_CODE_LS_KEY);
      const cartLandingIds = cartStorage.getLandingIds();
      const dataToSend = {
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
        successUrl: `${BASE_URL}${Path.successPayment}`,
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
          Alert(
            t("successPaymentWithBalance", { balance: balanceLeft }),
            <CheckMark />,
          );
          navigate(Path.profile);
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

  console.log(
    !paymentData.source ? getPaymentSource(isOffer) : paymentData.source,
  );

  return (
    <div className={s.modal}>
      <div className={s.courses}>
        {paymentData.courses.map((course, index: number) => (
          <div key={index} className={s.course}>
            <p>
              {course.name}{" "}
              {!isWebinar && (
                <>
                  - <span className={"highlight"}>{course.lessonsCount}</span>
                </>
              )}
            </p>
            {!isFree ? (
              <div className={s.course_prices}>
                <span className={"highlight"}>${course.newPrice}</span>
                <span className={"crossed"}>${course.oldPrice}</span>
              </div>
            ) : (
              <p className={s.free_text}>
                <Trans i18nKey={"firstFreeLesson"} />
              </p>
            )}
          </div>
        ))}
      </div>
      <div className={s.total_container}>
        {isLogged && !isFree && (
          <div className={s.balance_container}>
            <p>
              <Trans i18nKey="cart.balance" />:<span> ${balance}</span>
            </p>
            <div className={s.checkbox_container}>
              <ToggleCheckbox
                disabled={balance! === 0}
                variant={"small"}
                onChange={handleCheckboxToggle}
                isChecked={isBalanceUsed}
              />
              <Trans i18nKey="cart.useBalance" />
            </div>
          </div>
        )}
        {!isFree && (
          <div className={`${s.total_text} ${!isLogged ? s.center : ""}`}>
            <Trans i18nKey="total" />
            <div>
              <span className={"highlight"}>
                ${isBalanceUsed ? balancePrice : paymentData.newPrice}
              </span>
              <span className={"crossed"}>${paymentData.oldPrice}</span>
            </div>
          </div>
        )}
      </div>
      {isFree && !isLogged && (
        <h3>
          <Trans i18nKey={"freeCourse.registerToWatch"} />
        </h3>
      )}
      <Form handleSubmit={handleSubmit(handlePayment)}>
        {!isLogged && (
          <>
            <Input
              id="name"
              placeholder={t("yourName")}
              error={errors.name?.message}
              {...register("name")}
            />
            <div>
              <Input
                id="email"
                placeholder={t("email")}
                error={errors.email?.message}
                {...register("email")}
              />
              {!isFree && (
                <p className={s.modal_text}>
                  <Trans i18nKey="emailGrant" />
                </p>
              )}
            </div>
            {isFree && (
              <Input
                type={"password"}
                id="password"
                placeholder={t("password")}
                error={errors.password?.message}
                {...register("password")}
              />
            )}
          </>
        )}
        <Button
          variant={"filled"}
          loading={loading}
          text={isFree ? "tryCourseForFree" : "pay"}
          type="submit"
        />
      </Form>

      <>
        {!isLogged && (
          <p className={s.modal_text}>
            {isFree ? (
              <Trans i18nKey="freePaymentWarn" />
            ) : (
              <Trans i18nKey="paymentWarn" />
            )}
          </p>
        )}
        {!isFree && (
          <ul className={s.logos}>
            {logos.map((Logo, index) => (
              <li key={index}>
                <Logo width="100%" height="100%" />
              </li>
            ))}
          </ul>
        )}
      </>
    </div>
  );
};

export default PaymentModal;
