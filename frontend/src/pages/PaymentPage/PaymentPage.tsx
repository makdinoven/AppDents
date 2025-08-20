import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../store/store.ts";
import { useSearchParams } from "react-router-dom";
import PaymentModal from "./content/PaymentModal/PaymentModal.tsx";
import { useEffect } from "react";
import { PAYMENT_PAGE_KEY } from "../../common/helpers/commonConstants.ts";
import { getLandingDataForPayment } from "../../store/actions/paymentActions.ts";
import { usePaymentModalHandler } from "../../common/hooks/usePaymentModalHandler.ts";

//TODO
//      УБРАТЬ ИЗ PAYMENTMODAL ВСЮ ЛОГИКУ
//      РАЗДЕЛИТЬ НА НЕСКОЛЬКО КОМПОНЕНТОВ ПО КОНТЕНТУ
//      ПРОКИДЫВАТЬ SOURCE ИЗВНЕ
//      УДАЛИТЬ ISWEBINAR И ISFREE

const PaymentPage = () => {
  const dispatch = useDispatch<AppDispatchType>();
  const { isPaymentModalOpen, paymentModalType } = usePaymentModalHandler();
  const [searchParams] = useSearchParams();
  const slug = searchParams.get(PAYMENT_PAGE_KEY);
  const data = useSelector((state: AppRootStateType) => state.payment.data);

  useEffect(() => {
    if (isPaymentModalOpen) {
      if (!data && slug) {
        dispatch(getLandingDataForPayment(slug));
      }
    }
  }, [searchParams, data, isPaymentModalOpen]);

  if (!data) return;

  return (
    <PaymentModal
      isWebinar={paymentModalType === "webinar"}
      isFree={paymentModalType === "free"}
      isOffer={paymentModalType === "offer"}
      visibleCondition={isPaymentModalOpen}
      paymentData={data}
    />
  );
};

export default PaymentPage;
