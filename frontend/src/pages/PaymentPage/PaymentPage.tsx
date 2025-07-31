import { useDispatch, useSelector } from "react-redux";
import { AppRootStateType } from "../../store/store.ts";
import { useSearchParams } from "react-router-dom";
import PaymentModal from "./content/PaymentModal/PaymentModal.tsx";
import { useEffect } from "react";
import {
  closePaymentModal,
  openPaymentModal,
  setPaymentData,
} from "../../store/slices/paymentSlice.ts";
import { PAYMENT_PAGE_KEY } from "../../common/helpers/commonConstants.ts";
import { mainApi } from "../../api/mainApi/mainApi.ts";
import ModalOverlay from "../../components/Modals/ModalOverlay/ModalOverlay.tsx";

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
  const dispatch = useDispatch();

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
          fetchPaymentData();
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

  useEffect(() => {
    console.log(hasOpenKey, data);
  }, [hasOpenKey]);

  const fetchPaymentData = async () => {
    try {
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
    } catch (e) {
      console.error(e);
      handleClose();
    }
  };

  if (!data) return;

  return (
    <ModalOverlay
      customHandleClose={handleClose}
      isVisibleCondition={isOpen && !!data}
      modalPosition="center"
    >
      <PaymentModal
        isWebinar={data.isWebinar}
        isFree={data.isFree}
        isOffer={data.isOffer}
        paymentData={data}
      />
    </ModalOverlay>
  );
};

export default PaymentPage;
