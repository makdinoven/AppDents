import s from "./CommonModalStyles.module.scss";
import { t } from "i18next";
import { useForm } from "../../common/hooks/useForm.ts";
import Form from "./modules/Form/Form.tsx";
import Input from "./modules/Input/Input.tsx";
import Button from "../ui/Button/Button.tsx";
import { ChangePasswordType } from "../../api/userApi/types.ts";
import { emailSchema } from "../../common/schemas/emailSchema.ts";

const PaymentModal = ({
  handlePayment,
  isLogged,
}: {
  handlePayment: any;
  isLogged: boolean;
}) => {
  const { values, errors, handleChange, handleSubmit } =
    useForm<ChangePasswordType>({
      validationSchema: isLogged ? undefined : emailSchema,
      onSubmit: (email) => handlePayment(email),
    });

  return (
    <div className={s.modal}>
      <Form handleSubmit={handleSubmit}>
        {!isLogged && (
          <Input
            id="email"
            name="email"
            value={values.email || ""}
            placeholder={t("email")}
            onChange={handleChange}
            error={errors?.email}
          />
        )}
        <Button text={t("pay")} type="submit" />
      </Form>
    </div>
  );
};

export default PaymentModal;
