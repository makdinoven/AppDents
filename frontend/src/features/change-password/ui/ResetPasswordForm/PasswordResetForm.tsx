import s from "./PasswordResetForm.module.scss";
import { Trans } from "react-i18next";
import Form from "../../../../shared/components/Modals/modules/Form/Form.tsx";
import { t } from "i18next";
import Button from "../../../../shared/components/ui/Button/Button.tsx";
import { userApi } from "@/shared/api/userApi/userApi.ts";
import { useSelector } from "react-redux";
import { AppRootStateType } from "@/shared/store/store.ts";
import { resetPasswordSchema } from "@/shared/common/schemas/resetPasswordSchema.ts";
import { ResetPasswordType } from "@/shared/api/userApi/types.ts";
import { joiResolver } from "@hookform/resolvers/joi";
import { useForm } from "react-hook-form";
import { Alert } from "@/shared/components/ui/Alert/Alert.tsx";
import { AlertCirceIcon, CheckMark } from "../../../../shared/assets/icons";
import PasswordInput from "../../../../shared/components/ui/Inputs/PasswordInput/PasswordInput.tsx";
import { useState } from "react";

export const PasswordResetForm = () => {
  const { id } = useSelector((state: AppRootStateType) => state.user);
  const language = useSelector(
    (state: AppRootStateType) => state.user.language,
  );
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordType>({
    resolver: joiResolver(resetPasswordSchema),
    mode: "onSubmit",
  });
  const [loading, setLoading] = useState<boolean>(false);

  const handleResetPassword = async (newPassword: any) => {
    if (id) {
      try {
        setLoading(true);
        await userApi.resetPassword(newPassword, id);
        Alert(t("passwordChanged"), <CheckMark />);
      } catch {
        setLoading(false);
        Alert(t("error.errorChangingPassword"), <AlertCirceIcon />);
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <Form handleSubmit={handleSubmit(handleResetPassword)}>
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
