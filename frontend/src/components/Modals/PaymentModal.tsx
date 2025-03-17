import s from "./CommonModalStyles.module.scss";
import { t } from "i18next";
import { useForm } from "../../common/hooks/useForm.ts";
import Form from "./modules/Form.tsx";
import Input from "./modules/Input.tsx";
import Button from "../ui/Button/Button.tsx";
import { ChangePasswordType } from "../../api/userApi/types.ts";
import { emailSchema } from "../../common/schemas/emailSchema.ts";

const PaymentModal = ({
  title,
  onClose,
}: {
  title: string;
  onClose: () => void;
}) => {
  const { values, errors, handleChange, handleSubmit } =
    useForm<ChangePasswordType>({
      validationSchema: emailSchema,
      onSubmit: (data) => handlePayment(data),
    });

  const handlePayment = async (data: any) => {
    console.log(data);
    onClose();
  };

  return (
    <div className={s.modal}>
      <h3>{title}</h3>
      <Form handleSubmit={handleSubmit}>
        <>
          <Input
            id="email"
            name="email"
            value={values.email || ""}
            placeholder={t("email")}
            onChange={handleChange}
            error={errors?.email}
          />
          <Button text={t("pay")} type="submit" />
        </>
      </Form>
    </div>
  );
};

export default PaymentModal;
