import s from "./PasswordReset.module.scss";
import { Trans } from "react-i18next";
import Form from "../../../../../../../../components/Modals/modules/Form/Form.tsx";
import { t } from "i18next";
import Button from "../../../../../../../../components/ui/Button/Button.tsx";
import { userApi } from "../../../../../../../../api/userApi/userApi.ts";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../../../../../../store/store.ts";
import { resetPasswordSchema } from "../../../../../../../../common/schemas/resetPasswordSchema.ts";
import { ResetPasswordType } from "../../../../../../../../api/userApi/types.ts";
import { joiResolver } from "@hookform/resolvers/joi";
import { useForm } from "react-hook-form";
import { Alert } from "../../../../../../../../components/ui/Alert/Alert.tsx";
import {
  AlertCirceIcon,
  CheckMark,
} from "../../../../../../../../assets/icons";
import PasswordInput from "../../../../../../../../components/ui/Inputs/PasswordInput/PasswordInput.tsx";
import { useState } from "react";

const PasswordReset = () => {
  const { id } = useSelector((state: AppRootStateType) => state.user);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordType>({
    resolver: joiResolver(resetPasswordSchema),
    mode: "onTouched",
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
        <div className={s.reset_input}>
          <label htmlFor="new-password">
            <Trans i18nKey="passwordResetLabel" />
          </label>
          <PasswordInput
            id="new-password"
            placeholder={t("newPassword")}
            {...register("password")}
            error={errors.password?.message}
            {...{ variant: "admin" }}
          />
        </div>
        <div className={s.reset_button}>
          <Button
            text="reset"
            type="submit"
            variant="filled"
            loading={loading}
            disabled={loading}
          />
        </div>
      </div>
    </Form>
  );
};

export default PasswordReset;
