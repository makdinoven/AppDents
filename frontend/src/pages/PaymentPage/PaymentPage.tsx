import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../store/store.ts";
import { useSearchParams } from "react-router-dom";
import PaymentModal from "./content/PaymentModal/PaymentModal.tsx";
import { useEffect } from "react";
import {
  closePaymentModal,
  openPaymentModal,
} from "../../store/slices/paymentSlice.ts";
import { PAYMENT_PAGE_KEY } from "../../common/helpers/commonConstants.ts";
import { getLandingDataForPayment } from "../../store/actions/paymentActions.ts";

//TODO
//      УБРАТЬ ИЗ PAYMENTMODAL ВСЮ ЛОГИКУ
//      РАЗДЕЛИТЬ НА НЕСКОЛЬКО КОМПОНЕНТОВ ПО КОНТЕНТУ
//      ПРОКИДЫВАТЬ SOURCE ИЗВНЕ
//      УДАЛИТЬ ISWEBINAR И ISFREE

const PaymentPage = () => {
  const openKey = PAYMENT_PAGE_KEY;
  const [searchParams, setSearchParams] = useSearchParams();
  const slug = searchParams.get(openKey);
  const isOpen = useSelector(
    (state: AppRootStateType) => state.payment.isPaymentModalOpen,
  );
  const hasOpenKey = searchParams.has(openKey);
  const data = useSelector((state: AppRootStateType) => state.payment.data);

  const dispatch = useDispatch<AppDispatchType>();

  const handleClose = () => {
    const newParams = new URLSearchParams(searchParams);
    newParams.delete(openKey);
    setSearchParams(newParams);
    dispatch(closePaymentModal());
  };

  useEffect(() => {
    if (hasOpenKey) {
      if (!data) {
        if (slug) {
          dispatch(getLandingDataForPayment(slug));
        }
      } else {
        dispatch(openPaymentModal());
      }
    }
  }, [searchParams, data, hasOpenKey]);

  useEffect(() => {
    if (isOpen && !hasOpenKey) {
      const newParams = new URLSearchParams(searchParams);
      newParams.set(openKey, data?.slug ? data.slug : "");
      setSearchParams(newParams);
    }
  }, [isOpen, hasOpenKey]);

  // useEffect(() => {
  //   console.log(hasOpenKey, data);
  // }, [hasOpenKey]);

  if (!data) return;

  return (
    <PaymentModal
      isWebinar={data.isWebinar}
      isFree={data.isFree}
      isOffer={data.isOffer}
      handleClose={handleClose}
      visibleCondition={isOpen && !!data}
      paymentData={data}
    />
  );
};

export default PaymentPage;
