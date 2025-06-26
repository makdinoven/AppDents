import s from "./CommonModalStyles.module.scss";
import { Trans } from "react-i18next";
import ModalLink from "./modules/ModalLink/ModalLink.tsx";
import Form from "./modules/Form/Form.tsx";
import Input from "./modules/Input/Input.tsx";
import { t } from "i18next";
import Button from "../ui/Button/Button.tsx";
import { emailSchema } from "../../common/schemas/emailSchema.ts";
import { Path } from "../../routes/routes.ts";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { userApi } from "../../api/userApi/userApi.ts";
import { ChangePasswordType } from "../../api/userApi/types.ts";
import { joiResolver } from "@hookform/resolvers/joi";
import { useForm } from "react-hook-form";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../store/store.ts";
import { Alert } from "../ui/Alert/Alert.tsx";
import CheckMark from "../../assets/Icons/CheckMark.tsx";

const ForgotPasswordModal = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<any>(null);
  const navigate = useNavigate();
  const language = useSelector(
    (state: AppRootStateType) => state.user.language
  );
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ChangePasswordType>({
    resolver: joiResolver(emailSchema),
    mode: "onTouched",
  });

  const handleResetPassword = async (email: any) => {
    setLoading(true);
    try {
      await userApi.forgotPassword(email, language);
      Alert(t("forgotPasswordSuccess"), <CheckMark />);
      navigate("/login");
    } catch (error: any) {
      setError(error.response.data.detail.error.translation_key);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={s.modal}>
      <Form handleSubmit={handleSubmit(handleResetPassword)}>
        <>
          <Input
            id="email"
            placeholder={t("email")}
            error={errors.email?.message}
            {...register("email")}
          />
          <Button loading={loading} text={t("reset")} type="submit" />
        </>
      </Form>
      <div className={s.modal_bottom}>
        {error && (
          <p className={s.error_message}>
            <Trans i18nKey={error} />
          </p>
        )}
        <span>
          <Trans i18nKey={"passwordResetMailSent"} />
        </span>
        <ModalLink link={Path.login} text={"backToLogin"} />
      </div>
    </div>
  );
};

export default ForgotPasswordModal;
