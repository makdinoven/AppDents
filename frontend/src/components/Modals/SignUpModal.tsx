import s from "./CommonModalStyles.module.scss";
import { Trans } from "react-i18next";
import ModalLink from "./modules/ModalLink/ModalLink.tsx";
import Input from "./modules/Input/Input.tsx";
import { t } from "i18next";
import Button from "../ui/Button/Button.tsx";
import Form from "./modules/Form/Form.tsx";
import { useForm } from "../../common/hooks/useForm.ts";
import { emailSchema } from "../../common/schemas/emailSchema.ts";
import { Path } from "../../routes/routes.ts";
import { userApi } from "../../api/userApi/userApi.ts";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

const SignUpModal = () => {
  const [error, setError] = useState<any>(null);
  const navigate = useNavigate();
  const { values, errors, handleChange, handleSubmit } = useForm({
    validationSchema: emailSchema,
    onSubmit: (email) => handleSignUp(email),
  });

  const handleSignUp = async (email: any) => {
    try {
      await userApi.signUp(email);
      navigate("/login");
    } catch (error) {
      setError(error);
    }
  };

  return (
    <div className={s.modal}>
      <Form handleSubmit={handleSubmit}>
        <>
          <Input
            id="emailSignUp"
            name="email"
            value={values.email || ""}
            placeholder={t("email")}
            onChange={handleChange}
            error={errors?.email}
          />
          <Button text={t("signup")} type="submit" />
        </>
      </Form>
      <div className={s.modal_bottom}>
        {error?.response?.data?.detail?.error?.translation_key && (
          <p className={s.error_message}>
            <Trans i18nKey={error.response.data.detail.error.translation_key} />
          </p>
        )}
        <span>
          <Trans i18nKey={"alreadyHaveAccount"} />
        </span>
        <ModalLink variant={"uppercase"} link={Path.login} text={"login"} />
      </div>
    </div>
  );
};

export default SignUpModal;
