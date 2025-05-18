import { useForm } from "react-hook-form";
import { joiResolver } from "@hookform/resolvers/joi";
import { t } from "i18next";
import { Trans } from "react-i18next";
import s from "./PaymentModal.module.scss";
import Form from "../modules/Form/Form";
import Input from "../modules/Input/Input";
import Button from "../../ui/Button/Button";
import { PaymentType } from "../../../api/userApi/types";
import { paymentSchema } from "../../../common/schemas/paymentSchema";
import {
  AmexLogo,
  ApplePayLogo,
  DinnerClubLogo,
  DiscoverLogo,
  GooglePayLogo,
  JcbLogo,
  MastercardLogo,
  UnionPayLogo,
  VisaLogo,
} from "../../../assets/logos/index";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../store/store.ts";
import { mainApi } from "../../../api/mainApi/mainApi.ts";

const logos = [
  AmexLogo,
  ApplePayLogo,
  DinnerClubLogo,
  DiscoverLogo,
  GooglePayLogo,
  JcbLogo,
  MastercardLogo,
  UnionPayLogo,
  VisaLogo,
];

export type PaymentDataType = {
  course_ids: number[];
  price_cents: number;
  total_new_price: number;
  total_old_price: number;
  region: string;
  success_url: string;
  cancel_url: string;
  courses: { name: string; new_price: number; old_price: number }[];
};

const PaymentModal = ({
  paymentData,
  handleCloseModal,
}: {
  paymentData: PaymentDataType;
  handleCloseModal: () => void;
}) => {
  const { isLogged, email } = useSelector(
    (state: AppRootStateType) => state.user,
  );
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<PaymentType>({
    resolver: isLogged ? undefined : joiResolver(paymentSchema),
    mode: "onTouched",
  });

  const handlePayment = async (form: any) => {
    const dataToSend = {
      ...paymentData,
      user_email: isLogged ? email : form.email,
    };
    try {
      const res = await mainApi.buyCourse(dataToSend);
      const checkoutUrl = res.data.checkout_url;

      if (checkoutUrl) {
        const newTab = window.open(checkoutUrl, "_blank");

        if (!newTab || newTab.closed || typeof newTab.closed === "undefined") {
          window.location.href = checkoutUrl;
        } else {
          handleCloseModal();
        }
      } else {
        console.error("Checkout URL is missing");
      }
    } catch (error) {
      console.log(error);
    }
  };

  return (
    <div className={s.modal}>
      <div className={s.courses}>
        {paymentData.courses.map((course, index: number) => (
          <div key={index} className={s.course}>
            <p>{course.name}</p>
            <div className={s.course_prices}>
              <span className={"highlight"}>${course.new_price}</span>
              <span className={"crossed"}>${course.old_price}</span>
            </div>
          </div>
        ))}
      </div>
      <div className={s.total_text}>
        <Trans i18nKey="total" />
        <div>
          <span className={"highlight"}>${paymentData.total_new_price}</span>
          <span className={"crossed"}>${paymentData.total_old_price}</span>
        </div>
      </div>

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
              <p className={s.modal_text}>
                <Trans i18nKey="emailGrant" />
              </p>
            </div>
          </>
        )}
        <Button text={t("pay")} type="submit" />
      </Form>
      <p className={s.modal_text}>
        <Trans i18nKey="paymentWarn" />
      </p>

      <ul className={s.logos}>
        {logos.map((Logo, index) => (
          <li key={index}>
            <Logo width="100%" height="100%" />
          </li>
        ))}
      </ul>
    </div>
  );
};

export default PaymentModal;
