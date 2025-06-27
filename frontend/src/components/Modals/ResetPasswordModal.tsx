import s from "./CommonModalStyles.module.scss";
import { Trans } from "react-i18next";
import Form from "./modules/Form/Form.tsx";
import { t } from "i18next";
import Button from "../ui/Button/Button.tsx";
import { useState } from "react";
import { userApi } from "../../api/userApi/userApi.ts";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../store/store.ts";
import { resetPasswordSchema } from "../../common/schemas/resetPasswordSchema.ts";
import Input from "./modules/Input/Input.tsx";
import { ResetPasswordType } from "../../api/userApi/types.ts";
import { joiResolver } from "@hookform/resolvers/joi";
import { useForm } from "react-hook-form";
import { Alert } from "../ui/Alert/Alert.tsx";
import CheckMark from "../../assets/Icons/CheckMark.tsx";

const ResetPasswordModal = ({ handleClose }: { handleClose: () => void }) => {
  const [error, setError] = useState<any>(null);
  const { id } = useSelector((state: AppRootStateType) => state.user);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordType>({
    resolver: joiResolver(resetPasswordSchema),
    mode: "onTouched",
  });

  const handleResetPassword = async (newPassword: any) => {
    if (id) {
      try {
        await userApi.resetPassword(newPassword, id);
        Alert(t("passwordChanged"), <CheckMark />);
        handleClose();
      } catch (error) {
        setError(error);
        console.log(error);
      }
    }
  };

  return (
    <div className={s.modal}>
      <Form handleSubmit={handleSubmit(handleResetPassword)}>
        <>
          <Input
            type="password"
            id="password"
            placeholder={t("newPassword")}
            {...register("password")}
            error={errors.password?.message}
          />
          <Button text={"change"} type="submit" />
        </>
      </Form>
      {error && (
        <div className={s.modal_bottom}>
          <p className={s.error_message}>
            <Trans i18nKey={"error.errorChangingPassword"} />
          </p>
        </div>
      )}
    </div>
  );
};

export default ResetPasswordModal;
