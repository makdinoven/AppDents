import s from "./PasswordResetForm.module.scss";
import { Trans } from "react-i18next";
import Form from "@/shared/components/Modals/modules/Form/Form.tsx";
import { t } from "i18next";
import Button from "@/shared/components/ui/Button/Button.tsx";
import PasswordInput from "@/shared/components/ui/Inputs/PasswordInput/PasswordInput.tsx";
import { usePasswordResetForm } from "../../model/usePasswordResetForm";

export const PasswordResetForm = () => {
  const { register, handleSubmit, errors, loading, onSubmit, language } =
    usePasswordResetForm();

  return (
    <Form handleSubmit={handleSubmit(onSubmit)}>
      <div className={s.password_reset}>
        <label lang={language.toLowerCase()} htmlFor="new-password">
          <Trans i18nKey="passwordResetLabel" />
        </label>
        <div className={s.input_button_container}>
          <div className={s.reset_input}>
            <PasswordInput
              id="new-password"
              placeholder={t("newPassword")}
              {...register("password")}
              error={errors.password?.message}
              {...{ variant: "admin" }}
            />
          </div>
          <Button
            text="reset"
            type="submit"
            loading={loading}
            disabled={loading}
            className={s.reset_btn}
          />
        </div>
      </div>
    </Form>
  );
};
