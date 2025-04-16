import s from "./CommonModalStyles.module.scss";
import { Trans } from "react-i18next";
import ModalLink from "./modules/ModalLink/ModalLink.tsx";
import Form from "./modules/Form/Form.tsx";
import Input from "./modules/Input/Input.tsx";
import { t } from "i18next";
import Button from "../ui/Button/Button.tsx";
import { useForm } from "../../common/hooks/useForm.ts";
import { emailSchema } from "../../common/schemas/emailSchema.ts";
import { Path } from "../../routes/routes.ts";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { userApi } from "../../api/userApi/userApi.ts";

const ForgotPasswordModal = () => {
  const [error, setError] = useState<any>(null);
  const navigate = useNavigate();
  const { values, errors, handleChange, handleSubmit } = useForm({
    validationSchema: emailSchema,
    onSubmit: (data) => handleResetPassword(data),
  });

  const handleResetPassword = async (email: any) => {
    try {
      await userApi.forgotPassword(email);
      navigate("/login");
    } catch (error: any) {
      setError(error.response.data.detail.error.translation_key);
    }
  };

  return (
    <div className={s.modal}>
      <Form handleSubmit={handleSubmit}>
        <>
          <Input
            name="email"
            id="emailResetPassword"
            placeholder={t("email")}
            value={values.email || ""}
            onChange={handleChange}
            error={errors?.email}
          />
          <Button text={t("reset")} type="submit" />
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
