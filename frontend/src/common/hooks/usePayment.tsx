import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import { AppDispatchType, AppRootStateType } from "../../store/store.ts";
import { usePaymentPageHandler } from "./usePaymentPageHandler.ts";
import {
  BASE_URL,
  LS_TOKEN_KEY,
  REF_CODE_LS_KEY,
  REF_CODE_PARAM,
} from "../helpers/commonConstants.ts";
import { cartStorage } from "../../api/cartApi/cartStorage.ts";
import { getPaymentSource } from "../helpers/helpers.ts";
import { Path } from "../../routes/routes.ts";
import {
  clearUserBooks,
  clearUserCourses,
} from "../../store/slices/userSlice.ts";
import { mainApi } from "../../api/mainApi/mainApi.ts";
import { getMe } from "../../store/actions/userActions.ts";
import { LanguagesType } from "../../components/ui/LangLogo/LangLogo.tsx";
import { PaymentHookDataPayload } from "../../store/slices/paymentSlice.ts";
import { getCart } from "../../store/actions/cartActions.ts";
import { Alert } from "../../components/ui/Alert/Alert.tsx";
import { t } from "i18next";
import { CheckMark } from "../../assets/icons";

const IS_PAYMENT_DISABLED = false;

export const usePayment = ({
  paymentData,
  isFree = false,
  isOffer = false,
}: {
  paymentData: PaymentHookDataPayload;
  isFree?: boolean;
  isOffer?: boolean;
}) => {
  const { closePaymentModal } = usePaymentPageHandler();
  const dispatch = useDispatch<AppDispatchType>();
  const navigate = useNavigate();
  const { isLogged, email, language, balance } = useSelector(
    (s: AppRootStateType) => s.user,
  );
  const [loading, setLoading] = useState(false);
  const [isBalanceUsed, setIsBalanceUsed] = useState(false);
  const [emailValue, setEmailValue] = useState("");

  if (!paymentData) {
    return {
      loading: false,
      isBalanceUsed: false,
      toggleBalance: () => {},
      balancePrice: 0,
      handlePayment: () => {},
      balance: 0,
      language: language || "en",
      setEmailValue: () => {},
      IS_PAYMENT_DISABLED,
    };
  }

  const toggleBalance = () => {
    if (balance !== 0) setIsBalanceUsed(!isBalanceUsed);
  };

  const balancePrice = isBalanceUsed
    ? Math.round(Math.max(paymentData.new_price! - balance!, 0) * 100) / 100
    : paymentData.new_price;

  const handlePayment = async () => {
    setLoading(true);

    try {
      if (isFree) {
        await handleFreePayment();
      } else {
        await handlePaidPayment();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handlePaidPayment = async () => {
    const rcCode = localStorage.getItem(REF_CODE_LS_KEY);
    const cartLandingIds = cartStorage.getLandingIds();

    const dataToSend = {
      book_ids: paymentData.book_ids,
      book_landing_ids: paymentData.book_landing_ids,
      from_ad: paymentData.from_ad,
      price_cents: paymentData.price_cents,
      region: paymentData.region || (language as LanguagesType),
      landing_ids: paymentData.landing_ids,
      course_ids: paymentData.course_ids,
      use_balance: isBalanceUsed,
      user_email: isLogged ? (email as string) : emailValue,
      transfer_cart: !isLogged,
      cart_landing_ids: cartLandingIds.cart_landing_ids,
      cart_book_landing_ids: cartLandingIds.cart_book_landing_ids,
      source: paymentData.source || getPaymentSource(isOffer),
      success_url: `${BASE_URL}${Path.successPayment}`,
      ...(rcCode && { ref_code: rcCode }),
      cancel_url:
        !isLogged && rcCode
          ? window.location.href + `?${REF_CODE_PARAM}=${rcCode}`
          : window.location.href,
    };

    const res = await mainApi.buyCourse(dataToSend, isLogged);
    const { checkout_url, balance_left } = res.data;

    localStorage.removeItem(REF_CODE_LS_KEY);

    if (checkout_url) {
      const newTab = window.open(checkout_url, "_blank");
      if (!newTab || newTab.closed || typeof newTab.closed === "undefined") {
        window.location.href = checkout_url;
      }
    }

    if (isBalanceUsed && balance_left) {
      await dispatch(getCart());
      Alert(
        `${t("successPaymentWithBalance", { balance: balance_left })}`,
        <CheckMark />,
      );
    }

    if (balance_left) {
      await dispatch(getMe());
      dispatch(clearUserCourses());
      dispatch(clearUserBooks());
      navigate(Path.profileMain);
    }
  };

  const handleFreePayment = async () => {
    const res = await mainApi.getFreeCourse(
      {
        id: paymentData.landing_ids[0],
        email: isLogged ? email : emailValue,
        region: paymentData.region || language,
      },
      isLogged,
    );

    if (isLogged) {
      navigate(Path.profileMain);
    } else {
      closePaymentModal();
      localStorage.setItem(LS_TOKEN_KEY, res.data.access_token);
      await dispatch(getMe());
      navigate(Path.profileMain);
    }
  };

  return {
    loading,
    isBalanceUsed,
    toggleBalance,
    balancePrice,
    handlePayment,
    balance,
    language,
    setEmailValue,
    IS_PAYMENT_DISABLED,
  };
};
