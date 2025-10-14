import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import { AppDispatchType, AppRootStateType } from "../../store/store.ts";
import {
  BASE_URL,
  LS_TOKEN_KEY,
  REF_CODE_LS_KEY,
  REF_CODE_PARAM,
} from "../helpers/commonConstants.ts";
import { cartStorage } from "../../api/cartApi/cartStorage.ts";
import { getPaymentSource } from "../helpers/helpers.ts";
import { Path } from "../../routes/routes.ts";
import { mainApi } from "../../api/mainApi/mainApi.ts";
import { getMe } from "../../store/actions/userActions.ts";
import { usePaymentPageHandler } from "./usePaymentPageHandler.ts";
import { clearUserCourses } from "../../store/slices/userSlice.ts";

const IS_PAYMENT_DISABLED = false;

export const usePayment = ({ paymentData, isFree, isOffer }: any) => {
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
    ? Math.round(Math.max(paymentData.newPrice - balance!, 0) * 100) / 100
    : paymentData.newPrice;

  const handlePayment = async () => {
    setLoading(true);

    if (!isFree) {
      const rcCode = localStorage.getItem(REF_CODE_LS_KEY);
      const cartLandingIds = cartStorage.getLandingIds();

      const dataToSend = {
        total_old_price: paymentData.oldPrice,
        total_new_price: paymentData.newPrice,
        from_ad: paymentData.fromAd,
        price_cents: paymentData.priceCents,
        region: paymentData.region || language,
        landing_ids: paymentData.landingIds,
        course_ids: paymentData.courseIds,
        use_balance: isBalanceUsed,
        user_email: isLogged ? email : emailValue,
        transfer_cart: !isLogged,
        cart_landing_ids: cartLandingIds,
        source: paymentData.source || getPaymentSource(isOffer),
        success_url: `${BASE_URL}${Path.successPayment}`,
        courses: paymentData.courses,
        cancel_url:
          !isLogged && rcCode
            ? window.location.href + `?${REF_CODE_PARAM}=${rcCode}`
            : window.location.href,
      };

      try {
        const res = await mainApi.buyCourse(dataToSend, isLogged);
        const { checkout_url, balance_left } = res.data;

        localStorage.removeItem(REF_CODE_LS_KEY);

        if (checkout_url) {
          const newTab = window.open(checkout_url, "_blank");
          if (
            !newTab ||
            newTab.closed ||
            typeof newTab.closed === "undefined"
          ) {
            window.location.href = checkout_url;
          }
        }

        if (balance_left) {
          await dispatch(getMe());
          dispatch(clearUserCourses());
          navigate(Path.profile);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    } else {
      try {
        const res = await mainApi.getFreeCourse(
          {
            id: paymentData.landingIds[0],
            email: isLogged ? email : emailValue,
            region: paymentData.region || language,
          },
          isLogged,
        );

        if (isLogged) {
          navigate(Path.profile);
        } else {
          closePaymentModal();
          localStorage.setItem(LS_TOKEN_KEY, res.data.access_token);
          await dispatch(getMe());
          navigate(Path.profile);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
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
