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

const PaymentModal = ({
  courseName,
  price,
  handlePayment,
  isLogged,
}: {
  price: string;
  courseName: string;
  handlePayment: (data: PaymentType) => void;
  isLogged: boolean;
}) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<PaymentType>({
    resolver: isLogged ? undefined : joiResolver(paymentSchema),
    mode: "onTouched",
  });

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

  return (
    <div className={s.modal}>
      <div className={s.course_name_wrapper}>
        <p>{courseName}</p>
        <span>{price}</span>
      </div>
      <p className={s.total_text}>
        <Trans i18nKey="total" /> {price}
      </p>

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
