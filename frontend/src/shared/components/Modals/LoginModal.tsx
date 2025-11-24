import s from "./CommonModalStyles.module.scss";
import { Trans } from "react-i18next";
import { t } from "i18next";
import { loginSchema } from "../../common/schemas/loginSchema.ts";
import Form from "./modules/Form/Form.tsx";
import Button from "../ui/Button/Button.tsx";
import ModalLink from "./modules/ModalLink/ModalLink.tsx";
import { getMe, login } from "../../store/actions/userActions.ts";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../store/store.ts";
import { LoginType } from "../../api/userApi/types.ts";
import { joiResolver } from "@hookform/resolvers/joi";
import { useForm } from "react-hook-form";
import { useState } from "react";
import PasswordInput from "../ui/Inputs/PasswordInput/PasswordInput.tsx";
import EmailInput from "../ui/Inputs/EmailInput/EmailInput.tsx";
import { PATHS } from "../../../app/routes/routes.ts";

const LoginModal = () => {
  const [loading, setLoading] = useState(false);
  const dispatch = useDispatch<AppDispatchType>();
  const { error } = useSelector((state: AppRootStateType) => state.user);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginType>({
    resolver: joiResolver(loginSchema),
    mode: "onTouched",
  });

  const handleLogIn = async (data: LoginType) => {
    setLoading(true);

    const loginResponse = await dispatch(login(data));

    if (loginResponse.meta.requestStatus === "fulfilled") {
      await dispatch(getMe());
    } else {
    }

    setLoading(false);
  };

  return (
    <div className={s.modal}>
      <Form handleSubmit={handleSubmit(handleLogIn)}>
        <>
          <div className={s.inputs}>
            <EmailInput
              isValidationUsed={false}
              id="email"
              error={errors.email?.message}
              placeholder={t("email")}
              {...register("email")}
            />
            <PasswordInput
              id="password"
              placeholder={t("password")}
              {...register("password")}
              error={errors.password?.message}
            />
          </div>
          <Button
            loading={loading}
            text={t("login")}
            type="submit"
            variant="filled_light"
          />
        </>
      </Form>
      <div className={s.modal_bottom}>
        {error?.detail?.error?.translation_key && (
          <p className={s.error_message}>
            <Trans i18nKey={error.detail.error.translation_key} />
          </p>
        )}
        <span>
          <Trans i18nKey={"firstTimeHere"} />
          <ModalLink
            variant={"uppercase"}
            link={PATHS.SIGN_UP}
            text={"signup"}
          />
        </span>
        <ModalLink link={PATHS.PASSWORD_RESET} text={"forgotPassword"} />
      </div>
    </div>
  );
};

export default LoginModal;
