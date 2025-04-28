import s from "./CommonModalStyles.module.scss";
import { Trans } from "react-i18next";
import ModalLink from "./modules/ModalLink/ModalLink.tsx";
import Input from "./modules/Input/Input.tsx";
import { t } from "i18next";
import Button from "../ui/Button/Button.tsx";
import Form from "./modules/Form/Form.tsx";
import { emailSchema } from "../../common/schemas/emailSchema.ts";
import { Path } from "../../routes/routes.ts";
import { userApi } from "../../api/userApi/userApi.ts";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ChangePasswordType } from "../../api/userApi/types.ts";
import { joiResolver } from "@hookform/resolvers/joi";
import { useForm } from "react-hook-form";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../store/store.ts";

const SignUpModal = () => {
  const [error, setError] = useState<any>(null);
  const navigate = useNavigate();
  const language = useSelector(
    (state: AppRootStateType) => state.user.language,
  );
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ChangePasswordType>({
    resolver: joiResolver(emailSchema),
    mode: "onTouched",
  });

  const handleSignUp = async (email: any) => {
    try {
      await userApi.signUp(email, language);
      alert(t("registrationSuccess"));
      navigate("/login");
    } catch (error) {
      setError(error);
    }
  };

  return (
    <div className={s.modal}>
      <Form handleSubmit={handleSubmit(handleSignUp)}>
        <>
          <Input
            id="emailSignUp"
            placeholder={t("email")}
            {...register("email")}
            error={errors.email?.message}
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
