import ModalWrapper from "../../components/Modals/ModalWrapper/ModalWrapper.tsx";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../store/store.ts";
import { useNavigate, useParams } from "react-router-dom";
import PaymentModal from "../../components/Modals/PaymentModal/PaymentModal.tsx";

//TODO
//      УБРАТЬ ИЗ PAYMENTMODAL ВСЮ ЛОГИКУ
//      РАЗДЕЛИТЬ НА НЕСКОЛЬКО КОМПОНЕНТОВ ПО КОНТЕНТУ
//      ПРОКИДЫВАТЬ SOURCE ИЗВНЕ
//      УДАЛИТЬ ISWEBINAR И ISFREE
//      УДАЛИТЬ ОТСЮДА MODAL WRAPPER

const PaymentPage = () => {
  const navigate = useNavigate();
  const { slug } = useParams();
  const data = useSelector((state: AppRootStateType) => state.payment.data);
  const isFree = useSelector(
    (state: AppRootStateType) => state.payment.data?.isFree,
  );
  const isWebinar = useSelector(
    (state: AppRootStateType) => state.payment.data?.isWebinar,
  );
  // const dispatch = useDispatch();
  console.log(slug);

  if (!data) {
    console.log("запрос за данными для оплаты, если их нет в редаксе");
  }

  const handleClose = () => {
    navigate(-1);
  };

  // useEffect(() => {
  //   return () => {
  //     dispatch(clearPaymentData());
  //   };
  // }, []);

  return (
    <ModalWrapper
      variant="dark"
      title={"yourOrder"}
      cutoutPosition="none"
      isOpen={true}
      onClose={handleClose}
    >
      <PaymentModal
        isWebinar={isWebinar}
        isFree={isFree}
        paymentData={data!} //TODO УДАЛИТЬ !
        handleCloseModal={handleClose}
      />
    </ModalWrapper>
  );
};

export default PaymentPage;
