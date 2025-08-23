import s from "./PaymentForm.module.scss";
import Input from "../../../../components/ui/Inputs/Input/Input.tsx";
import { t } from "i18next";
import EmailInput from "../../../../components/ui/Inputs/EmailInput/EmailInput.tsx";
import { useForm } from "react-hook-form";
import { PaymentType } from "../../../../api/userApi/types.ts";
import { joiResolver } from "@hookform/resolvers/joi";
import { paymentSchema } from "../../../../common/schemas/paymentSchema.ts";
import { useEffect } from "react";

const PaymentForm = ({
  isLogged,
  setEmail,
  isFree,
}: {
  isFree?: boolean;
  isLogged: boolean;
  setEmail: (email: string) => void;
}) => {
  const {
    register,
    watch,
    setValue,
    formState: { errors },
  } = useForm<PaymentType>({
    resolver: isLogged ? undefined : joiResolver(paymentSchema),
    mode: "onTouched",
  });

  const emailInputName = "email";
  const emailValue = watch(emailInputName);

  useEffect(() => {
    if (emailValue) setEmail(emailValue);
  }, [emailValue]);

  return (
    <>
      <div className={`${s.form_inputs} ${isFree ? s.free : ""}`}>
        <Input id="name" placeholder={t("yourName")} {...register("name")} />
        <EmailInput
          isValidationUsed
          id="email"
          value={emailValue}
          setValue={setValue}
          error={errors.email?.message}
          placeholder={t("email")}
          {...register(emailInputName)}
        />
        {isFree && (
          <Input
            id="password"
            placeholder={t("password")}
            {...register("password")}
          />
        )}
      </div>
    </>
  );
};

export default PaymentForm;
