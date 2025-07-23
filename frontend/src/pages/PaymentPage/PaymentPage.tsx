import ModalWrapper from "../../components/Modals/ModalWrapper/ModalWrapper.tsx";
import { useDispatch, useSelector } from "react-redux";
import { AppRootStateType } from "../../store/store.ts";
import { useSearchParams } from "react-router-dom";
import PaymentModal from "../../components/Modals/PaymentModal/PaymentModal.tsx";
import { useEffect } from "react";
import {
  closePaymentModal,
  openPaymentModal,
  setPaymentData,
} from "../../store/slices/paymentSlice.ts";
import { PAYMENT_PAGE_KEY } from "../../common/helpers/commonConstants.ts";
import { mainApi } from "../../api/mainApi/mainApi.ts";

//TODO
//      УБРАТЬ ИЗ PAYMENTMODAL ВСЮ ЛОГИКУ
//      РАЗДЕЛИТЬ НА НЕСКОЛЬКО КОМПОНЕНТОВ ПО КОНТЕНТУ
//      ПРОКИДЫВАТЬ SOURCE ИЗВНЕ
//      УДАЛИТЬ ISWEBINAR И ISFREE
//      УДАЛИТЬ ОТСЮДА MODAL WRAPPER

const PaymentPage = () => {
  const openKey = PAYMENT_PAGE_KEY;
  const [searchParams, setSearchParams] = useSearchParams();
  const slug = searchParams.get(openKey);
  const isOpen = useSelector(
    (state: AppRootStateType) => state.payment.isPaymentModalOpen,
  );
  const hasOpenKey = searchParams.has(openKey);
  const data = useSelector((state: AppRootStateType) => state.payment.data);
  const dispatch = useDispatch();

  const clearParams = () => {
    const newParams = new URLSearchParams(searchParams);
    newParams.delete(openKey);
    setSearchParams(newParams);
  };

  const setParams = () => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set(openKey, data?.slug ? data.slug : "");
    setSearchParams(newParams);
  };

  const handleClose = () => {
    clearParams();
    dispatch(closePaymentModal());
    // dispatch(clearPaymentData());
  };

  useEffect(() => {
    if (hasOpenKey) {
      if (!data) {
        if (slug) {
          fetchPaymentData();
        }
      } else {
        dispatch(openPaymentModal());
      }
    }
  }, [searchParams, data, hasOpenKey]);

  useEffect(() => {
    if (isOpen && !hasOpenKey) {
      setParams();
    }
  }, [isOpen]);

  const fetchPaymentData = async () => {
    const res = await mainApi.getLanding(slug);
    dispatch(
      setPaymentData({
        landingIds: [res.data?.id],
        courseIds: res.data?.course_ids,
        priceCents: res.data?.new_price * 100,
        newPrice: res.data?.new_price,
        oldPrice: res.data?.old_price,
        region: res.data?.language,
        slug: res.data?.page_name,
        fromAd: false,
        // source: "!!!!!!!!!!!!!!!!!!",
        courses: [
          {
            name: res.data?.landing_name,
            newPrice: res.data?.new_price,
            oldPrice: res.data?.old_price,
            lessonsCount: res.data?.lessons_count,
          },
        ],
      }),
    );
  };

  return (
    isOpen &&
    data && (
      <ModalWrapper
        variant="dark"
        title={"yourOrder"}
        cutoutPosition="none"
        isOpen={true}
        onClose={handleClose}
      >
        <PaymentModal
          isWebinar={data.isWebinar}
          isFree={data.isFree}
          isOffer={data.isOffer}
          paymentData={data}
        />
      </ModalWrapper>
    )
  );
};

export default PaymentPage;
