import s from "./PaymentForm.module.scss";
import Input from "../../../../shared/components/ui/Inputs/Input/Input.tsx";
import { t } from "i18next";
import EmailInput from "../../../../shared/components/ui/Inputs/EmailInput/EmailInput.tsx";
import { useForm } from "react-hook-form";
import { PaymentType } from "../../../../shared/api/userApi/types.ts";
import { joiResolver } from "@hookform/resolvers/joi";
import { paymentSchema } from "../../../../shared/common/schemas/paymentSchema.ts";
import { useEffect } from "react";

const PaymentForm = ({
  isLogged,
  setEmail,
  isFree,
  onRegisterValidate, // <— ДОБАВИЛИ
}: {
  isFree?: boolean;
  isLogged: boolean;
  setEmail: (email: string) => void;
  onRegisterValidate?: (fn: () => Promise<boolean>) => void; // <—
}) => {
  const {
    register,
    watch,
    setValue,
    trigger, // <— НУЖНО
    setFocus, // <— опционально: сразу фокус на email при ошибке
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

  useEffect(() => {
    if (!onRegisterValidate) return;
    onRegisterValidate(async () => {
      const ok = await trigger(); // валидируем всю форму (или trigger("email"))
      if (!ok) {
        // опционально — фокус на email, если он пуст/невалиден
        if (errors.email) setFocus("email");
      }
      return ok;
    });
  }, [onRegisterValidate, trigger, errors.email, setFocus]);

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
