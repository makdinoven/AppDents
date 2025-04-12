import s from "./CommonModalStyles.module.scss";
import { Trans } from "react-i18next";
import Form from "./modules/Form/Form.tsx";
import Input from "./modules/Input/Input.tsx";
import { t } from "i18next";
import Button from "../ui/Button/Button.tsx";
import { useForm } from "../../common/hooks/useForm.ts";
import { useState } from "react";
import { userApi } from "../../api/userApi/userApi.ts";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../store/store.ts";
import { resetPasswordSchema } from "../../common/schemas/resetPasswordSchema.ts";

const ResetPasswordModal = ({ handleClose }: { handleClose: () => void }) => {
  const [error, setError] = useState<any>(null);
  const { values, errors, handleChange, handleSubmit } = useForm({
    validationSchema: resetPasswordSchema,
    onSubmit: (data) => handleResetPassword(data),
  });
  const id = useSelector((state: AppRootStateType) => state.user.id);

  const handleResetPassword = async (newPassword: any) => {
    if (id) {
      try {
        await userApi.resetPassword(newPassword, id);
        alert(t("passwordChanged"));
        handleClose();
      } catch (error) {
        setError(error);
        console.log(error);
      }
    }
  };

  return (
    <div className={s.modal}>
      <Form handleSubmit={handleSubmit}>
        <>
          <Input
            name="password"
            id="password"
            placeholder={t("newPassword")}
            value={values.password || ""}
            onChange={handleChange}
            error={errors?.password}
          />
          <Button text={"change"} type="submit" />
        </>
      </Form>
      <div className={s.modal_bottom}>
        {error && (
          <p className={s.error_message}>
            <Trans i18nKey={"error.errorChangingPassword"} />
          </p>
        )}
      </div>
    </div>
  );
};

export default ResetPasswordModal;
