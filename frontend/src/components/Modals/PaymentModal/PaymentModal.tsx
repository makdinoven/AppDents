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
} from "../../../assets/logos";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../../store/store.ts";
import { mainApi } from "../../../api/mainApi/mainApi.ts";
import { useState } from "react";
import ToggleCheckbox from "../../ui/ToggleCheckbox/ToggleCheckbox.tsx";
import {
  LS_TOKEN_KEY,
  PAYMENT_SOURCES,
  REF_CODE_LS_KEY,
  REF_CODE_PARAM,
} from "../../../common/helpers/commonConstants.ts";
import { cartStorage } from "../../../api/cartApi/cartStorage.ts";
import { useNavigate } from "react-router-dom";
import { Path } from "../../../routes/routes.ts";
import { PaymentType } from "../../../api/userApi/types.ts";
import { getMe } from "../../../store/actions/userActions.ts";
import { Alert } from "../../ui/Alert/Alert.tsx";
import { CheckMark } from "../../../assets/icons/index.ts";

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

export type PaymentDataType = {
  landing_ids?: number[];
  course_ids: number[];
  price_cents: number;
  total_new_price: number;
  total_old_price: number;
  region: string;
  success_url: string;
  cancel_url: string;
  source?: string;
  courses: {
    name: string;
    new_price: number;
    old_price: number;
    lessons_count: string;
  }[];
};

const PaymentModal = ({
  isOffer = false,
  isWebinar = false,
  isFree = false,
  paymentData,
  handleCloseModal,
}: {
  isWebinar?: boolean;
  isFree?: boolean;
  isOffer?: boolean;
  paymentData: PaymentDataType;
  handleCloseModal: () => void;
}) => {
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

  const getPaymentSource = () => {
    const pathname = location.pathname.startsWith("/")
      ? location.pathname
      : "/" + location.pathname;

    const sources = PAYMENT_SOURCES.filter((s) => {
      const isCorrectType = isOffer
        ? s.name.endsWith("_OFFER")
        : !s.name.endsWith("_OFFER");
      return isCorrectType && s.path && pathname.startsWith(s.path);
    });

    const sorted = sources.sort((a, b) => b.path.length - a.path.length);
    return sorted[0]?.name || "OTHER";
  };

  const balancePrice = isBalanceUsed
    ? Math.round(Math.max(paymentData.total_new_price - balance!, 0) * 100) /
      100
    : paymentData.total_new_price;

  const handlePayment = async (form: any) => {
    setLoading(true);
    if (!isFree) {
      const rcCode = localStorage.getItem(REF_CODE_LS_KEY);
      const cartLandingIds = cartStorage.getLandingIds();
      const dataToSend = {
        ...paymentData,
        use_balance: isBalanceUsed,
        user_email: isLogged ? email : form.email,
        transfer_cart: !isLogged && cartLandingIds.length > 0,
        cart_landing_ids: cartLandingIds,
        source: !paymentData.source ? getPaymentSource() : paymentData.source,
        cancel_url:
          !isLogged && rcCode
            ? paymentData.cancel_url + `?${REF_CODE_PARAM}=${rcCode}`
            : paymentData.cancel_url,
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
          } else {
            handleCloseModal();
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
        id: paymentData.landing_ids![0],
        email: isLogged ? email : form.email,
        region: paymentData.region,
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

  return (
    <div className={s.modal}>
      <div className={s.courses}>
        {paymentData.courses.map((course, index: number) => (
          <div key={index} className={s.course}>
            <p>
              {course.name}{" "}
              {!isWebinar && (
                <>
                  - <span className={"highlight"}>{course.lessons_count}</span>
                </>
              )}
            </p>
            {!isFree ? (
              <div className={s.course_prices}>
                <span className={"highlight"}>${course.new_price}</span>
                <span className={"crossed"}>${course.old_price}</span>
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
                ${isBalanceUsed ? balancePrice : paymentData.total_new_price}
              </span>
              <span className={"crossed"}>${paymentData.total_old_price}</span>
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
