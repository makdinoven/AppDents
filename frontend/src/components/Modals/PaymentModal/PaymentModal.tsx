import s from "./PaymentModal.module.scss";
import { t } from "i18next";
import { useForm } from "../../../common/hooks/useForm.ts";
import Form from "../modules/Form/Form.tsx";
import Input from "../modules/Input/Input.tsx";
import Button from "../../ui/Button/Button.tsx";
import { PaymentType } from "../../../api/userApi/types.ts";
import { paymentSchema } from "../../../common/schemas/paymentSchema.ts";
import { Trans } from "react-i18next";
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
  handlePayment: any;
  isLogged: boolean;
}) => {
  const { values, errors, handleChange, handleSubmit } = useForm<PaymentType>({
    validationSchema: isLogged ? undefined : paymentSchema,
    onSubmit: (email) => handlePayment(email),
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
        <p> {courseName}</p>
        <span>{price}</span>
      </div>
      <p className={s.total_text}>
        <Trans i18nKey={"total"} /> {price}
      </p>
      <Form handleSubmit={handleSubmit}>
        {!isLogged && (
          <>
            <Input
              id="name"
              name="name"
              value={values.name || ""}
              placeholder={t("yourName")}
              onChange={handleChange}
              error={errors?.name}
            />
            <div>
              <Input
                id="email"
                name="email"
                value={values.email || ""}
                placeholder={t("email")}
                onChange={handleChange}
                error={errors?.email}
              />
              <p className={s.modal_text}>
                <Trans i18nKey={"emailGrant"} />
              </p>
            </div>
          </>
        )}
        <Button text={t("pay")} type="submit" />
      </Form>
      <p className={s.modal_text}>
        <Trans i18nKey={"paymentWarn"} />
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
