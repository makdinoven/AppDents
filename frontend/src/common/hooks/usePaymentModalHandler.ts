import { useSearchParams } from "react-router-dom";
import {
  PAYMENT_PAGE_KEY,
  PAYMENT_TYPE_KEY,
  PAYMENT_TYPES,
} from "../helpers/commonConstants.ts";

type PaymentType = (typeof PAYMENT_TYPES)[keyof typeof PAYMENT_TYPES];

export const usePaymentModalHandler = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const isPaymentModalOpen = searchParams.has(PAYMENT_PAGE_KEY);
  const paymentModalType = searchParams.get(PAYMENT_TYPE_KEY);

  const openPaymentModal = (slug?: string, type?: PaymentType) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set(PAYMENT_PAGE_KEY, slug ?? "");
    setSearchParams(newParams);

    if (type) {
      const updatedParams = new URLSearchParams(newParams);
      updatedParams.set(PAYMENT_TYPE_KEY, type);
      setSearchParams(updatedParams, { replace: true });
    }
  };

  const closePaymentModal = () => {
    const paramsHasPaymentType = searchParams.has(PAYMENT_TYPE_KEY);
    const newParams = new URLSearchParams(searchParams);

    newParams.delete(PAYMENT_PAGE_KEY);
    setSearchParams(newParams);

    if (paramsHasPaymentType) {
      setTimeout(() => {
        const updatedParams = new URLSearchParams(newParams);
        updatedParams.delete(PAYMENT_TYPE_KEY);
        setSearchParams(updatedParams, { replace: true });
      }, 150);
    }
  };

  return {
    isPaymentModalOpen,
    openPaymentModal,
    closePaymentModal,
    paymentModalType,
  };
};
