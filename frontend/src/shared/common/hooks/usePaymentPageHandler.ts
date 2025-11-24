import { useSearchParams } from "react-router-dom";
import {
  PAYMENT_MODE_KEY,
  PAYMENT_PAGE_KEY,
  PAYMENT_TYPE_KEY,
  PAYMENT_TYPES,
} from "../helpers/commonConstants.ts";

type PaymentType = (typeof PAYMENT_TYPES)[keyof typeof PAYMENT_TYPES];
export type PaymentDataModeType = "COURSES" | "BOOKS" | "BOTH";

export const usePaymentPageHandler = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const isPaymentModalOpen = searchParams.has(PAYMENT_PAGE_KEY);
  const paymentModalType = searchParams.get(PAYMENT_TYPE_KEY);
  const paymentModalMode = searchParams.get(PAYMENT_MODE_KEY);
  const slug = searchParams.get(PAYMENT_PAGE_KEY);

  const openPaymentModal = (
    slug?: string,
    type?: PaymentType,
    mode: PaymentDataModeType = "COURSES",
  ) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set(PAYMENT_PAGE_KEY, slug ?? "");
    setSearchParams(newParams);
    let updatedParams;

    if (type) {
      updatedParams = new URLSearchParams(newParams);
      updatedParams.set(PAYMENT_TYPE_KEY, type);
      setSearchParams(updatedParams, { replace: true });
    }

    if (mode) {
      const updatedParamsMode = new URLSearchParams(
        type ? updatedParams : newParams,
      );
      updatedParamsMode.set(PAYMENT_MODE_KEY, mode);
      setSearchParams(updatedParamsMode, { replace: true });
    }
  };

  const closePaymentModal = () => {
    setTimeout(() => {
      const newParams = new URLSearchParams(searchParams);
      newParams.delete(PAYMENT_PAGE_KEY);
      if (paymentModalType) newParams.delete(PAYMENT_TYPE_KEY);
      if (paymentModalMode) newParams.delete(PAYMENT_MODE_KEY);
      setSearchParams(newParams);
    }, 150);
  };

  return {
    isPaymentModalOpen,
    openPaymentModal,
    closePaymentModal,
    paymentModalType,
    paymentModalMode,
    slug,
  };
};
